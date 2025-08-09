#!/bin/bash
set -e

echo "🎭 Downloading Dolphin Mixtral 8x7B Q4_K_M..."
cd /home/anthon/t0v4/tova_v4/data/models/

# Create models directory if it doesn't exist
mkdir -p /home/anthon/t0v4/tova_v4/data/models/

# Download Dolphin Mixtral 8x7B Q4_K_M
wget -c https://huggingface.co/TheBloke/dolphin-2.7-mixtral-8x7b-GGUF/resolve/main/dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf

echo "✅ Model download complete!"
echo "📍 Model location: /home/anthon/t0v4/tova_v4/data/models/dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf"
