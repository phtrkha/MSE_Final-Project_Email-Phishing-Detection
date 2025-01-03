class Config:
    CURRENT_MODEL = "GPT-3.5-TURBO"  # Giá trị mặc định, có thể thay đổi sang "BERT" hoặc "GPT"
    
    @classmethod
    def set_current_model(cls, model_name):
        if model_name in ["NAIVE-BAYES", "LSTM", "GRU", "GPT-3.5-TURBO", "GPT-4"]:
            cls.CURRENT_MODEL = model_name
            return True
        return False

    @classmethod
    def get_current_model(cls):
        return cls.CURRENT_MODEL