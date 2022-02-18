if [[ $(command -v brew) == "" ]]; then
    echo "Installing Hombrew"
    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
else
    echo "Found Homebrew"
fi

if [[ $(command -v ffmpeg) == "" ]]; then
    echo "Installing ffmpeg"
    brew install ffmpeg
else
    echo "Found ffmpeg"
fi

chmod +x ./gui
spctl --add ./gui
chmod +x ./gui

# ./gui.command