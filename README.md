# Prerequisites

* [Homebrew](https://brew.sh/index_ja)
* Python 3.6 or above
* [SoX](http://sox.sourceforge.net/sox.html)
* [PortAudio](http://www.portaudio.com/)

```
brew install sox portaudio
```

# Install

```
git clone https://github.com/hiraro/gcp_speech_to_text_sample_py.git

cd gcp_speech_to_text_sample_py

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.sample` as `.env`

```
cp .env.sample .env
```

Finally, copy your [GOOGLE_APPLICATION_CREDENTIALS](https://cloud.google.com/speech-to-text/docs/quickstart-client-libraries) file as `google_cloud_speech_service_account.json` into cloned directory.

```
ls -la gcp_speech_to_text_sample_py
.
.
.
-rw-r--r--  1 user staff 2.4K 11  1 17:34 google_cloud_speech_service_account.json
.
.
.
```

# Usage

```
./start.sh
```

Will output `output/yyyymmddHHMM.wav` and its parts as `output/yyyymmddHHMM.wav-n.wav`.
