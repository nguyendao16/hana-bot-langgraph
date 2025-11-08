# Setup script cho Hana Chatbot với TTS
# Tự động cài đặt tất cả dependencies bao gồm PyTorch CUDA

Write-Host "Setting up Hana Chatbot Environment..." -ForegroundColor Green
Write-Host ""

# Step 1: Remove old environment if exists
Write-Host "Step 1: Checking for existing environment..." -ForegroundColor Cyan
$envExists = conda env list | Select-String "hana"
if ($envExists) {
    Write-Host "   Found existing 'hana' environment. Removing..." -ForegroundColor Yellow
    conda env remove -n hana -y
    Write-Host "   ✓ Old environment removed" -ForegroundColor Green
} else {
    Write-Host "   ✓ No existing environment found" -ForegroundColor Green
}
Write-Host ""

# Step 2: Create conda environment
Write-Host "Step 2: Creating conda environment from YAML..." -ForegroundColor Cyan
conda env create -f hana_conda_environment.yml
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ✗ Failed to create environment" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ Conda environment created" -ForegroundColor Green
Write-Host ""

# Step 3: Install PyTorch with CUDA (theo hướng dẫn RealtimeSTT)
Write-Host "Step 3: Installing PyTorch with CUDA 12.1..." -ForegroundColor Cyan
conda activate hana
pip install torch==2.5.1+cu121 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ✗ Failed to install PyTorch" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ PyTorch with CUDA installed" -ForegroundColor Green
Write-Host ""

# Step 4: Verify installation
Write-Host "Step 4: Verifying installation..." -ForegroundColor Cyan
Write-Host "   Checking Python version..." -ForegroundColor Gray
python --version

Write-Host "   Checking PyTorch..." -ForegroundColor Gray
python -c "import torch; print(f'   PyTorch: {torch.__version__}'); print(f'   CUDA Available: {torch.cuda.is_available()}')"

Write-Host "   Checking TorchAudio..." -ForegroundColor Gray
python -c "import torchaudio; print(f'   TorchAudio: {torchaudio.__version__}')"

Write-Host "   Checking SSL Certificate..." -ForegroundColor Gray
python -c "import certifi; print(f'   SSL Cert: {certifi.where()}')"

Write-Host ""
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "   1. Make sure Redis is running (port 6379)" -ForegroundColor White
Write-Host "   2. Make sure PostgreSQL is running (port 5432)" -ForegroundColor White
Write-Host "   3. Run TTS server: python voice/hana_tts.py" -ForegroundColor White
Write-Host "   4. Run Chatbot: python main.py" -ForegroundColor White
Write-Host ""
