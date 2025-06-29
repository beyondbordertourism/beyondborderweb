// Hero Video Management
document.addEventListener('DOMContentLoaded', function() {
    const video = document.querySelector('.hero-video');
    const heroSection = document.querySelector('.hero-section');
    
    if (video && heroSection) {
        // Handle video loading
        video.addEventListener('canplay', function() {
            video.classList.add('loaded');
            video.style.display = 'block';
            video.style.opacity = '1';
        });
        
        video.addEventListener('canplaythrough', function() {
            video.play().catch(e => {
                console.log('Video autoplay prevented:', e.message);
            });
        });
        
        video.addEventListener('error', function(e) {
            console.error('Video failed to load:', e.type);
            video.style.display = 'none';
        });
        
        // Force load the video
        video.load();
        
        // Pause video when not in viewport (performance optimization)
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && video.classList.contains('loaded')) {
                    video.play().catch(e => console.log('Video autoplay prevented in viewport'));
                } else {
                    video.pause();
                }
            });
        }, { threshold: 0.25 });
        
        observer.observe(heroSection);
        
        // Handle reduced motion preference
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            video.pause();
            video.style.display = 'none';
        }
    }
}); 