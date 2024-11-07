const targetTime = new Date();
targetTime.setHours(24, 0, 0, 0);
const totalMilliseconds = 24 * 60 * 60 * 1000;
const progressBar = document.getElementById('progress-bar');
const countdownTimer = document.getElementById('countdown-timer');

function updateCountdown() {
    const now = new Date();
    const timeDiff = targetTime - now;
    const hours = Math.floor(timeDiff / (1000 * 60 * 60));
    const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);

    // Update the countdown timer
    countdownTimer.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

    // Update the progress bar
    const progressPercentage = ((totalMilliseconds - timeDiff) / totalMilliseconds) * 100;
    progressBar.style.width = `${progressPercentage}%`;

    if (timeDiff > 0) {
        requestAnimationFrame(updateCountdown);
    }
}

updateCountdown();
