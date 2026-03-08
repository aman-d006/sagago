from datetime import datetime, timedelta
import pytz

IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """Get current time in IST"""
    return datetime.now(IST)

def utc_to_ist(utc_dt):
    """Convert UTC datetime to IST"""
    if utc_dt.tzinfo is None:
        utc_dt = pytz.UTC.localize(utc_dt)
    return utc_dt.astimezone(IST)

def format_ist_time(dt):
    """Format datetime for display in IST"""
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    ist_dt = dt.astimezone(IST)
    
    now = get_ist_now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    
    if ist_dt.date() == today:
        return f"Today at {ist_dt.strftime('%I:%M %p')}"
    elif ist_dt.date() == yesterday:
        return f"Yesterday at {ist_dt.strftime('%I:%M %p')}"
    else:
        return ist_dt.strftime('%d %b %Y at %I:%M %p')