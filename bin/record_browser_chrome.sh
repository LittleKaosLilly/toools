#!/bin/bash
# Get pulseaudio monitor sink monitor device then pipe it to 
# sox to record ogg, wav, mp3 or flac.
# The point was to record directly from the sink source
# and not the audio device output.
#
# Collection linked to my errand on the big net...
# might have forgoten to record some source. Sorry about that.
#
# Source (in desorder):
# https://www.pantz.org/software/alsa/recording_sound_from_your_web_browser_using_linux.html
# man sox
# https://sox.fandom.com/wiki/EFFECTS
# https://outflux.net/blog/archives/2009/04/19/recording-from-pulseaudio/
# https://unix.stackexchange.com/questions/45837/pipe-the-output-of-parec-to-sox
# https://stackoverflow.com/questions/18091464/what-is-the-effect-of-the-quality-option-in-sox-mp3-compression
# https://unix.stackexchange.com/questions/85455/convert-wav-music-library-to-flac-on-command-line-and-achieve-best-quality

FILENAME="$1"
STOPTIME="$2"
# Encoding options for lame and flac.
SILENCE_R="5.0"
# SILENCE="1 10 0.1% 1 2.0 0.1%"
SILENCE="1 10 0.1% 1 ${SILENCE_R} 0.1%"

if [ -z "${FILENAME}" ]; then
    echo -e "
    Usage: $0 /path/to/output.wav or output.mp3 or output.flac
    Usage: $0 /path/to/output.wav or output.mp3 or output.flac stopinseconds
    stopinseconds: 0 mean autostop after ${SILENCE_R} seconds" >&2
    exit 1
fi

if [ -z ${STOPTIME} ]; then
    echo -e "\nno Stop time."
elif [ "A${STOPTIME}" == "A0" ]; then
    echo -e "\nAuto-stopping after ${SILENCE_R} seconds blank."
else
  if [[ ${STOPTIME} =~ : ]]; then
    STOPT=$(echo "${STOPTIME}" | sed 's/:\|-/ /g;' | awk '{print $4" "$3" "$2" "$1}' | awk '{print $1+$2*60+$3*3600+$4*86400}')
    STOPTIME=${STOPT}
  fi
  echo -e "\nStopping in ${STOPTIME} seconds."
fi

# Rip Audio from application using Pulseaudio (no Jack):
# get index number of application audio:
# * pacmd list-sink-inputs
#
# assuming index is $INDEX:
# pactl load-module module-null-sink sink_name=steam
# pactl move-sink-input $INDEX steam
# parec -d steam.monitor | sox -t raw -r 44k -sLb 16 -c 2 - /tmp/testme.wav

SINK_LST=$(pacmd list-sink-inputs | grep "sink input(s) available")
echo "$SINK_LST"
if [ "A$SINK_LST" == "A0 sink input(s) available." ]; then
  echo "no sink available"
  exit 1
fi

INDEX=$(pacmd list-sink-inputs | grep -P "Chromium|^    index:" | grep -B1 Chromium | grep 'index:' | sed 's/^ *index: //')
# The first command will add a null-sink as you already knew.
pactl load-module module-null-sink sink_name=steam
# The second command moves the sink-input from your standard-audio-sink to steam
pactl move-sink-input $INDEX steam
# The third command records the monitor of the device steam (-d) and puts the output (raw-wave-stream)
# parec -d steam.monitor
MONITOR="steam.monitor"

# OLD way Get sink monitor:
#MONITOR=$(pactl list | egrep -A2 '^(\*\*\* )?Source #' | \
#    grep 'Name: .*\.monitor$' | awk '{print $NF}' | tail -n1)
#echo "set-source-mute ${MONITOR} false" | pacmd >/dev/null

# try to detect silence, new file each time from man
# rec -r 44100 -b 16 -e signed-integer -p silence 1 0.50 0.1% 1 10:00 0.1% | sox -p output.ogg silence 1 0.50 0.1% 1 2.0 0.1% : newfile : restart

# Record it raw, and pipe to lame for an mp3
echo "Recording to ${FILENAME} ..."

if [[ ${FILENAME} =~ .ogg$ ]]; then
  if [ -z ${STOPTIME} ]; then
    parec -d "${MONITOR}" | sox -t raw -b 16 -e signed -c 2 -r 44100 - "${FILENAME}"
  elif [ "A${STOPTIME}" == "A0" ]; then
    echo -e "\nAuto-stopping after ${SILENCE_R} seconds blank"
    parec -d "${MONITOR}" | sox -t raw -b 16 -e signed -c 2 -r 44100 - "${FILENAME}" silence ${SILENCE} 
  else
    echo -e "\nStopping in ${STOPTIME} seconds"
    parec -d "${MONITOR}" | sox -t raw -b 16 -e signed -c 2 -r 44100 - "${FILENAME}" trim 0 ${STOPTIME}
  fi
  ogginfo "${FILENAME}"

elif [[ ${FILENAME} =~ .wav$ ]]; then
  # Note: wav has a limit of about 6.5hrs using 44k 16bit.
  echo "# Note: wav has a limit of about 6.5hrs using 44k 16bit." 
  if [ -z ${STOPTIME} ]; then
    parec -d "${MONITOR}" | sox -t raw -r 44k -sLb 16 -c 2 - "${FILENAME}"
  elif [ "A${STOPTIME}" == "A0" ]; then
    echo -e "\nAuto-stopping after ${SILENCE_R} seconds blank"
    parec -d "${MONITOR}" | sox -t raw -r 44k -sLb 16 -c 2 - "${FILENAME}" silence ${SILENCE}
  else
    echo -e "\nStopping in ${STOPTIME} seconds"
    parec -d "${MONITOR}" | sox -t raw -r 44k -sLb 16 -c 2 - "${FILENAME}" trim 0 ${STOPTIME}
  fi

# Not really working
elif [[ ${FILENAME} =~ .mp3$ ]]; then
  if [ -z ${STOPTIME} ]; then
    parec -d "${MONITOR}" | sox -t raw -r 44k -sLb 16 -c 2 - -C 192.02 "${FILENAME}"
  elif [ "A${STOPTIME}" == "A0" ]; then
    echo -e "\nAuto-stopping after ${SILENCE_R} seconds blank"
    parec -d "${MONITOR}" | sox -t raw -r 44k -sLb 16 -c 2 - -C 192.02 "${FILENAME}" silence ${SILENCE}
  else
    echo -e "\nStopping in ${STOPTIME} seconds"
    parec -d "${MONITOR}" | sox -t raw -r 44k -sLb 16 -c 2 - -C 192.02 "${FILENAME}" trim 0 ${STOPTIME}
  fi

elif [[ ${FILENAME} =~ .flac$ ]]; then
  if [ -z ${STOPTIME} ]; then
    parec -d "${MONITOR}" | sox -t raw -b 16 -e signed -c 2 - "${FILENAME}"
  elif [ "A${STOPTIME}" == "A0" ]; then
    echo -e "\nAuto-stopping after ${SILENCE_R} seconds blank"
    parec -d "${MONITOR}" | sox -t raw -b 16 -e signed -c 2 - "${FILENAME}" silence ${SILENCE} 
  else
    echo -e "\nStopping in ${STOPTIME} seconds"
    parec -d "${MONITOR}" | sox -t raw -b 16 -e signed -c 2 - "${FILENAME}" trim 0 ${STOPTIME}
  fi

else
  echo "Unknown audio format"
  exit 1
fi
soxi "${FILENAME}"
