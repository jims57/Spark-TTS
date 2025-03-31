@app.on_event("startup")
async def startup_event():
    """Load model on startup to avoid loading it on each request"""
    global global_model, global_device, global_is_half
    
    logger.info("Initializing Spark-TTS API...")
    
    # Set device
    if torch.cuda.is_available():
        global_device = 0
        logger.info(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        global_device = "cpu"
        logger.info("CUDA is not available. Using CPU.")
    
    # Initialize the model by running a dummy inference
    try:
        sys.argv = [
            "cli.inference",
            "--text", "Test initialization",
            "--device", str(global_device),
            "--save_dir", DEFAULT_SAVE_DIR,
            "--model_dir", MODEL_DIR,
            "--prompt_text", DEFAULT_PROMPT_TEXT,
            "--prompt_speech_path", DEFAULT_PROMPT_SPEECH_PATH
        ]
        inference.main()
        global_model = True  # Just to indicate model is loaded
        logger.info("Model initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model: {str(e)}")
        raise 