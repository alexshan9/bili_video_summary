from bilix.sites.bilibili import DownloaderBilibili
import asyncio


async def main():
    async with DownloaderBilibili() as d:
        await d.get_video(url="https://www.bilibili.com/video/BV1THstzuEZ9/?spm_id_from=333.1007.tianma.2-2-5.click&vd_source=921cdbee881bbccb979df87009cef4cc", only_audio=True)


asyncio.run(main())