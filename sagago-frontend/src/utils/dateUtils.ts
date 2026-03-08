// utils/dateUtils.ts
export const formatISTTime = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    
    // Convert to IST (UTC+5:30)
    const istOffset = 5.5 * 60 * 60 * 1000; // 5.5 hours in milliseconds
    const istTime = new Date(date.getTime() + istOffset);
    
    const now = new Date();
    const nowIST = new Date(now.getTime() + istOffset);
    
    const today = nowIST.toDateString();
    const yesterday = new Date(nowIST.getTime() - 24 * 60 * 60 * 1000).toDateString();
    const messageDate = istTime.toDateString();
    
    if (messageDate === today) {
      return `Today at ${istTime.toLocaleTimeString('en-IN', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })}`;
    } else if (messageDate === yesterday) {
      return `Yesterday at ${istTime.toLocaleTimeString('en-IN', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })}`;
    } else {
      return istTime.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    }
  } catch (e) {
    console.error('Error formatting date:', e);
    return dateString;
  }
};

export const formatISTTimeShort = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    
    // Convert to IST (UTC+5:30)
    const istOffset = 5.5 * 60 * 60 * 1000;
    const istTime = new Date(date.getTime() + istOffset);
    
    const now = new Date();
    const nowIST = new Date(now.getTime() + istOffset);
    
    const diffInHours = (nowIST.getTime() - istTime.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return istTime.toLocaleTimeString('en-IN', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      });
    } else if (diffInHours < 48) {
      return 'Yesterday';
    } else {
      return istTime.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short'
      });
    }
  } catch (e) {
    return dateString;
  }
};