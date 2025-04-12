document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const navbar = document.getElementById('navbar');
    let lastScroll = 0;

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            themeToggle.textContent = document.body.classList.contains('dark-mode') ? '☀' : '🌙';
        });
    }

    window.addEventListener('scroll', () => {
        const currentScroll = window.scrollY;
        if (currentScroll > lastScroll && currentScroll > 50) {
            navbar.classList.add('hidden');
        } else {
            navbar.classList.remove('hidden');
        }
        lastScroll = currentScroll;
    });

    document.querySelectorAll('.listen-btn').forEach(button => {
        button.addEventListener('click', () => {
            alert('Listening feature coming soon!');
        });
    });
});
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const navbar = document.getElementById('navbar');
    let lastScroll = 0;

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            themeToggle.textContent = document.body.classList.contains('dark-mode') ? '☀' : '🌙';
        });
    }

    window.addEventListener('scroll', () => {
        const currentScroll = window.scrollY;
        if (currentScroll > lastScroll && currentScroll > 50) {
            navbar.classList.add('hidden');
        } else {
            navbar.classList.remove('hidden');
        }
        lastScroll = currentScroll;
    });

    document.querySelectorAll('.listen-btn').forEach(button => {
        button.addEventListener('click', () => {
            alert('Listening feature coming soon!');
        });
    });

    document.querySelectorAll('.summarise-btn').forEach(button => {
        button.addEventListener('click', () => {
            alert('AI summary coming soon!');
        });
    });
});