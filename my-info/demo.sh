#!/bin/bash

# Check if required directories exist
if [ ! -d "pretrained_models/Spark-TTS-0.5B" ]; then
    echo "❌ Error: Model directory not found at pretrained_models/Spark-TTS-0.5B"
    exit 1
fi

if [ ! -f "example/prompt_audio.wav" ]; then
    echo "❌ Error: Prompt audio file not found at example/prompt_audio.wav"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "example/results"

echo "🎵 Starting Spark-TTS Text-to-Speech Generation 🎵"
echo "------------------------------------------------"
echo "📋 Configuration:"
echo "   - Model: Spark-TTS-0.5B"
echo "   - Input text: 'A beautiful melody is created note by note, each one essential to the whole.'"
echo "   - Output directory: example/results"
echo "------------------------------------------------"
echo "⏳ Processing... Please wait..."

# Run the TTS model
python -m cli.inference \
    --text "A beautiful melody is created note by note, each one essential to the whole." \
    --device 0 \
    --save_dir "example/results" \
    --model_dir "pretrained_models/Spark-TTS-0.5B" \
    --prompt_text "吃燕窝就选燕之屋，本节目由26年专注高品质燕窝的燕之屋冠名播出。豆奶牛奶换着喝，营养更均衡，本节目由豆本豆豆奶特约播出。" \
    --prompt_speech_path "example/prompt_audio.wav"

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo "✨ Success! Audio has been generated"
    echo "📂 Output saved in: example/results"
    echo "🎧 You can now check your generated audio file"
else
    echo "❌ Error: Something went wrong during processing"
    echo "   Please check the error messages above"
    exit 1
fi 