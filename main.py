import praw
import requests
import os


def download_gif(index, counter, submission, path):
    r = requests.get(submission.url)
    file = open(f"{path}raw_gif{counter:03}.gif", "wb")
    file.write(r.content)
    file.close()
    print(f"{index}: {counter:03}.gif downloaded")


def download_vid(index, counter, submission, path):
    try:
        video_url = submission.media["reddit_video"]["fallback_url"]
        audio_url = video_url.rsplit("_", 1)[0] + "_audio.mp4?source=fallback"
        r_video = requests.get(video_url)
        file = open(f"{path}raw_video{counter:03}.mp4", "wb")
        file.write(r_video.content)
        file.close()
        r_video.close()

        r_audio = requests.get(audio_url)
        file = open(f"{path}raw_audio{counter:03}.mp3", "wb")
        file.write(r_audio.content)
        file.close()
        r_audio.close()
        print(f"{index}: {counter:03}.mp4 and {counter:03}.mp3 downloaded")

    except TypeError:
        print(f"{index}: TypeError, not downloaded")
        global vid_counter
        vid_counter -= 1


def handle_gif(counter, path, out_path):
    concat = '"concat:'
    for i in range(1, counter):
        gif_to_avi = f'ffmpeg -i {path}raw_gif{i:03}.gif -r 25 -c:v libx264 -preset ultrafast -crf 18 {path}final{i:03}.avi'
        concat += f'{path}final{i:03}.avi|'
        os.system(gif_to_avi)

    concat = concat[0:-1]  # remove the last "|" character
    concat += '"'

    out = 'ffmpeg -i ' + concat + f' -c:v libx264 -pix_fmt yuv420p {out_path}final_gif_to_vid.mp4 -y'
    os.system(out)


def handle_vid(counter, path, out_path):
    # combine video and audio
    for i in range(1, counter):
        if os.stat(f"{path}raw_audio{i:03}.mp3").st_size > 255:  # check if there is audio
            combine = f'ffmpeg -i {path}raw_video{i:03}.mp4 -i {path}raw_audio{i:03}.mp3 -c:v copy -c:a aac {path}combined{i:03}.mp4'  # combines mp4 and mp3
            # resize the video and make it ready for concat
            resize = f'ffmpeg -i {path}combined{i:03}.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:color=black" {path}final{i:03}.mp4'
            os.system(combine)
            os.system(resize)
        else:  # if no audio on the mp3 we send the mp4 straight for rezising
            resize = f'ffmpeg -i {path}raw_video{i:03}.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:color=black" {path}final{i:03}.mp4'
            os.system(resize)

    # store the files for concatenation on .txt file
    f = open("final.txt", "w+")
    for i in range(1, counter):
        f.write(f"file {path}final{i:03}.mp4\n")
    f.close()

    # concatenates all the mp4 videos into one video
    concat = f'ffmpeg -f concat -i final.txt -c:v libx264 -pix_fmt yuv420p {out_path}final_output.mp4 -y'
    os.system(concat)
    print(f"Final video completed @ {out_path}final_video.mp4")


# removes files in folder
def clear_folder(folder_name):  # folder_name should be string. ex: r"avi"
    files = [f for f in os.listdir(folder_name)]
    for file in files:
        os.remove(os.path.join(folder_name, file))


gif_counter = vid_counter = 1

temp_path = "temp/"  # temporary storage for raw files
output_path = "output/"  # final output path
clear_folder(temp_path)
#clear_folder(output_path)

reddit = praw.Reddit(client_id="my_client_id", client_secret="my_secret_id",
                     user_agent="my_user_agent")

sub = reddit.subreddit("dankmemes")

for i, submission in enumerate(sub.top(limit=10, time_filter="month")):
    extension = str(submission.url).rsplit(".", 1)[1]

    if extension == "gif":
        download_gif(i, gif_counter, submission, temp_path)
        gif_counter += 1

    elif extension[-2:] == "51":  # stored videos on reddit end with 51 for some reason
        download_vid(i, vid_counter, submission, temp_path)
        vid_counter += 1

    else:
        print(f"{i}: failed, {extension} not supported")

if gif_counter > 1:
    handle_gif(gif_counter, temp_path, output_path)
if vid_counter > 1:
    handle_vid(vid_counter, temp_path, output_path)
