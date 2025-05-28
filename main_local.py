from odd_asr import OddASR
from log import logger

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Your WAV file need to recoginze to text.")
    parser.add_argument("audio_path", type=str, help="Path to the input WAV file.")
    args = parser.parse_args()

    odd_asr = OddASR()

    try:
        result = odd_asr.recognize(args.audio_path)
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Error: {e}")
        