def format_time(milliseconds):
    hours = milliseconds // 3600000
    minutes = (milliseconds % 3600000) // 60000
    seconds = ((milliseconds % 3600000) % 60000) / 1000

    return f'{"0" if hours < 10 and hours > 0 else ""}{str(hours) + ":" if hours > 0 else ""}{minutes:02d}:{"0" if seconds < 10 else ""}{seconds:.0f}'