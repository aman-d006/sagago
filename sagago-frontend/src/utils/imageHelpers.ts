export const getImageUrl = (url?: string): string | null => {
  if (!url) {
    console.log('getImageUrl: No URL provided')
    return null
  }
  
  console.log('getImageUrl: Original URL:', url)
  
  if (url.startsWith('http')) {
    console.log('getImageUrl: Using HTTP URL directly:', url)
    return url
  }
  
  if (url.startsWith('/uploads')) {
    const fullUrl = `http://localhost:8000${url}`
    console.log('getImageUrl: Constructed full URL:', fullUrl)
    return fullUrl
  }
  
  if (url.startsWith('data:')) {
    console.log('getImageUrl: Using data URL')
    return url
  }
  
  const constructedUrl = `http://localhost:8000/uploads/stories/${url.split('/').pop()}`
  console.log('getImageUrl: Constructed from filename:', constructedUrl)
  return constructedUrl
}