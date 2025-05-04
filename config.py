from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

    # Токен вашего бота
    bot_token: str = Field(..., env='BOT_TOKEN')
    # Отображаемое имя бота в меню (можно переопределить через .env)
    bot_name: str = Field(
        'Тренировка ОГЭ по русскому языку',
        env='BOT_NAME'
    )
    # Путь до файла со статистикой
    stats_path: str = Field('data/stats.json', env='STATS_PATH')
    # Путь до CSV с заданиями
    tasks_path: str = Field('data/tasks.csv', env='TASKS_PATH')
    # Уровень логирования
    log_level: str = Field('INFO', env='LOG_LEVEL')

settings = Settings()
