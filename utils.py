def format_duration(duration_seconds):
    duration_seconds = int(duration_seconds)
    minutes, seconds = divmod(duration_seconds, 60)
    return f"{minutes:02}:{seconds:02}"