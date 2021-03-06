#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

import os
import shutil
from datetime import datetime

import youtube_dl

from anydlbot import LOGGER
from anydlbot.config import Config
from anydlbot.helper_funcs.extract_link import get_link
from anydlbot.plugins.uploader import upload_worker

# the Strings used for this "thing"
from translation import Translation


async def youtube_dl_call_back(_, update):
    cb_data = update.data
    # youtube_dl extractors
    tg_send_type, youtube_dl_format, youtube_dl_ext = cb_data.split("|")
    thumb_image_path = os.path.join(Config.WORK_DIR, str(update.from_user.id) + ".jpg")

    (
        youtube_dl_url,
        custom_file_name,
        youtube_dl_username,
        youtube_dl_password,
    ) = get_link(update.message.reply_to_message)
    if not custom_file_name:
        custom_file_name = "%(title)s.%(ext)s"
    await update.message.edit_caption(caption=Translation.DOWNLOAD_START)
    # description = Translation.CUSTOM_CAPTION_UL_FILE
    tmp_directory_for_each_user = os.path.join(
        Config.WORK_DIR, str(update.from_user.id)
    )
    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)
    download_directory = os.path.join(tmp_directory_for_each_user, custom_file_name)
    ytdl_opts = {
        "outtmpl": download_directory,
        "ignoreerrors": True,
        "nooverwrites": True,
        "continuedl": True,
        "noplaylist": True,
        "max_filesize": Config.TG_MAX_FILE_SIZE,
    }
    if youtube_dl_username and youtube_dl_password:
        ytdl_opts.update(
            {
                "username": youtube_dl_username,
                "password": youtube_dl_password,
            }
        )
    if "hotstar" in youtube_dl_url:
        ytdl_opts.update(
            {
                "geo_bypass_country": "IN",
            }
        )
    if tg_send_type == "audio":
        ytdl_opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": youtube_dl_ext,
                        "preferredquality": youtube_dl_format,
                    },
                    {"key": "FFmpegMetadata"},
                ],
            }
        )
    elif tg_send_type in ["video", "file"]:
        minus_f_format = youtube_dl_format
        if "youtu" in youtube_dl_url:
            minus_f_format = f"{youtube_dl_format}+bestaudio"
        ytdl_opts.update(
            {
                "format": minus_f_format,
                "postprocessors": [{"key": "FFmpegMetadata"}],
            }
        )

    start_download = datetime.now()
    with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
        info = ytdl.extract_info(youtube_dl_url, download=False)
        title = info.get("title", None)
        yt_task = ytdl.download([youtube_dl_url])

    if yt_task == 0:
        end_download = datetime.now()
        time_taken_for_download = (end_download - start_download).seconds
        await update.message.edit_caption(
            caption=f"Download took {time_taken_for_download} seconds.\n"
            + Translation.UPLOAD_START
        )
        upl = await upload_worker(update, title, tg_send_type, True, download_directory)
        LOGGER.info(upl)
        shutil.rmtree(tmp_directory_for_each_user, ignore_errors=True)
        LOGGER.info("Cleared temporary folder")
        os.remove(thumb_image_path)

        await update.message.delete()
