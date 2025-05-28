import time
import wave
import os

from flask import Blueprint, render_template, request, session, send_file, jsonify

# import app
from log import logger
from odd_asr_app import odd_asr

########################################
## main
########################################
bp = Blueprint('asr', __name__, url_prefix='')

@bp.route('/v1/asr', methods=['POST'])
def transcribe():
    """
    Receive an audio file from the client and return the transcribed text.
    """
    try:
        # Get the uploaded audio file
        audio_file = request.files.get('audio')
        if not audio_file:
            return jsonify({"error": "Invalid parameter. audio param is required."}), 400
        
        # get mode from request if provided
        mode = request.form.get('mode', "")  # mode should be a string like 'file', 'stream', 'pipeline'
        output_format = request.form.get('output_format', "txt")  # output_format should be a string like 'txt', 'srt', 'spk'
        hotwords = request.form.get('hotwords', "")  # hotwords should be a string like 'word1 word2'

        # Save the audio file to a temporary location
        temp_path = "temp_audio.wav"
        audio_file.save(temp_path)

        logger.info(f"Received audio and saved to: {temp_path}")

        # recognition with hotwords
        match mode:
            case "file":
                result = odd_asr.transcribe_file(temp_path, hotwords=hotwords, output_format=output_format)
            case "stream":
                result = odd_asr.transcribe_stream(temp_path, hotwords=hotwords, output_format=output_format)
            case _:
                result = odd_asr.transcribe_file(temp_path, hotwords=hotwords, output_format=output_format)
        
        logger.info(f"Recognized mode:{mode}, fmt={output_format}, result: {result}")

        # Delete the temporary file
        os.remove(temp_path)

        logger.info(f"Deleted temporary file: {temp_path}")

        # Return the recognition result
        return jsonify({"text": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
