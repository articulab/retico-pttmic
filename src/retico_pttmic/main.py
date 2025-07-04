import retico_pttmic as pttmic
import retico_core


def main(frame_length, rate):

    terminal_logger, _ = retico_core.log_utils.configurate_logger()

    mic = pttmic.PTTMicrophoneModule(frame_length=frame_length, rate=rate)
    spk = retico_core.audio.SpeakerModule(rate=rate)
    mic.subscribe(spk)

    # running system
    try:
        retico_core.network.run(mic)
        terminal_logger.info("Dialog system running until ENTER key is pressed")
        input()
        retico_core.network.stop(mic)
    except Exception:
        terminal_logger.exception("exception in main")
        retico_core.network.stop(mic)


if __name__ == "__main__":

    frame_length = 0.02
    rate = 48000
    main(frame_length=frame_length, rate=rate)
