function convert(n) {
    var v = n < 0 ? n * 32768 : n * 32767;       // convert in range [-32768, 32767]
    return Math.max(-32768, Math.min(32768, v)); // clamp
}

class KAudioRecoder
{
    startRecoder(onFeed = function(){})
    {
        navigator.getUserMedia = navigator.getUserMedia ||
        navigator.webkitGetUserMedia ||
        navigator.mozGetUserMedia;
        if (!navigator.getUserMedia) 
        {
            alert('不支持音频输入');
            return;
        }
        this.audioContext = new AudioContext({sampleRate:16000});
        this.audioSource = null;
        this.audioProcessor = null;

        navigator.getUserMedia({ 
        audio: true,
        sampleRate:16000,
        sampleSize:16
        },function(stream){
            this.audioSource = this.audioContext.createMediaStreamSource(stream); 
            this.audioProcessor = this.audioContext.createScriptProcessor(2048,1,1)
            this.audioProcessor.onaudioprocess = function(e){
                var buffer = e.inputBuffer.getChannelData(0);
                var length = e.inputBuffer.getChannelData(0).length;
                var i16array = new Int16Array(length)
                for(var i = 0 ; i < length ; i++)
                {
                    i16array[i] = convert(buffer[i])
                }
                if (0!=onFeed((new Uint8Array(i16array.buffer)).buffer))
                {
                    this.stopRecoder();
                }
            }.bind(this)

            this.audioSource.connect(this.audioProcessor)
            this.audioProcessor.connect(this.audioContext.destination)
        }.bind(this),function(err){
            alert("open audio input failed")
            console.log("open audio input failed: ", err);
            this.state = ASR_CLIENT_EXCEPTION;
            this.onError(CODE.ASR_ERROR_INTER, err);
            this.onEnd(CODE.ASR_ERROR_INTER, err);
            this.onClose(CODE.ASR_ERROR_INTER, err);

        });
    }

    stopRecoder()
    {
        console.log("stop recorder: ", this.audioContext);

        if(this.audioProcessor != null)
        {
            this.audioSource.disconnect(this.audioProcessor)
            this.audioProcessor.disconnect(this.audioContext.destination)   
            this.audioProcessor = null;
            this.audioContext = null;  
        }
    }
}



 
