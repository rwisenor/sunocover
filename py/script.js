// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const targetTab = tab.dataset.tab;

        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        tab.classList.add('active');
        document.getElementById(targetTab).classList.add('active');
    });
});

// Search functionality
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const resultsContainer = document.getElementById('resultsContainer');
const songList = document.getElementById('songList');
let selectedSongUrl = null;

searchBtn.addEventListener('click', async () => {
    const query = searchInput.value.trim();
    if (!query) return;

    searchBtn.disabled = true;
    searchBtn.innerHTML = '<span class="btn-icon">⏳</span> Searching...';

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();

        if (data.error) {
            alert('Search failed: ' + data.error);
            return;
        }

        songList.innerHTML = '';
        data.results.forEach((song, index) => {
            const songItem = document.createElement('div');
            songItem.className = `song-item ${index === 0 ? 'selected' : ''}`;
            songItem.dataset.url = song.url;
            songItem.innerHTML = `
                <div class="song-radio"></div>
                <span>${song.title}</span>
            `;
            songItem.addEventListener('click', () => {
                document.querySelectorAll('.song-item').forEach(s => s.classList.remove('selected'));
                songItem.classList.add('selected');
                selectedSongUrl = song.url;
                checkInputs();
            });
            songList.appendChild(songItem);
        });

        if (data.results.length > 0) {
            selectedSongUrl = data.results[0].url;
        }

        resultsContainer.style.display = 'block';
        resultsContainer.style.animation = 'fadeIn 0.3s ease';

        document.querySelector('.success-badge').textContent = `✅ Found ${data.results.length} songs`;

        checkInputs();

    } catch (error) {
        console.error('Search error:', error);
        alert('Search failed: ' + error.message);
    } finally {
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<span class="btn-icon">🔍</span> Search';
    }
});

// Upload area
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
let uploadedFile = null;

uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--accent)';
    uploadArea.style.background = 'rgba(99, 102, 241, 0.1)';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = 'var(--border)';
    uploadArea.style.background = 'transparent';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--border)';
    uploadArea.style.background = 'transparent';

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    console.log('File selected:', file.name);
    uploadedFile = file;
    uploadArea.innerHTML = `
        <div class="upload-icon">✅</div>
        <p>${file.name}</p>
        <p class="upload-hint">Click to change file</p>
    `;
    checkInputs();
}

// YouTube URL
const youtubeUrl = document.getElementById('youtubeUrl');
const urlBtn = document.getElementById('urlBtn');
let currentYoutubeUrl = null;

urlBtn.addEventListener('click', () => {
    const url = youtubeUrl.value.trim();
    if (url && url.includes('youtube.com')) {
        currentYoutubeUrl = url;
        urlBtn.innerHTML = '<span class="btn-icon">✅</span> Loaded';
        checkInputs();
        setTimeout(() => {
            urlBtn.innerHTML = '<span class="btn-icon">🔗</span> Load';
        }, 2000);
    }
});

// Process button
const processBtn = document.getElementById('processBtn');
const outputPlaceholder = document.getElementById('outputPlaceholder');
const processingStatus = document.getElementById('processingStatus');
const audioPlayer = document.getElementById('audioPlayer');
const enhancedMode = document.getElementById('enhancedMode');

// Disable process button initially
processBtn.disabled = true;
processBtn.style.opacity = '0.5';
processBtn.style.cursor = 'not-allowed';

// Enable/disable process button based on input
function checkInputs() {
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    let hasInput = false;

    if (activeTab === 'search' && selectedSongUrl) {
        hasInput = true;
    } else if (activeTab === 'youtube' && currentYoutubeUrl) {
        hasInput = true;
    } else if (activeTab === 'upload' && uploadedFile) {
        hasInput = true;
    }

    processBtn.disabled = !hasInput;
    processBtn.style.opacity = hasInput ? '1' : '0.5';
    processBtn.style.cursor = hasInput ? 'pointer' : 'not-allowed';
}

// Check inputs on tab change
document.querySelectorAll('.tab').forEach(tab => {
    const originalClick = tab.onclick;
    tab.addEventListener('click', () => {
        setTimeout(checkInputs, 100);
    });
});

processBtn.addEventListener('click', async () => {
    if (processBtn.disabled) return;
    // Get input source
    let youtubeUrlToProcess = null;

    // Check which tab is active
    const activeTab = document.querySelector('.tab.active').dataset.tab;

    if (activeTab === 'search' && selectedSongUrl) {
        youtubeUrlToProcess = selectedSongUrl;
    } else if (activeTab === 'youtube' && currentYoutubeUrl) {
        youtubeUrlToProcess = currentYoutubeUrl;
    } else if (activeTab === 'upload' && uploadedFile) {
        alert('File upload processing not yet implemented');
        return;
    } else {
        alert('Please provide a song (search, URL, or upload file)');
        return;
    }

    outputPlaceholder.style.display = 'none';
    processingStatus.style.display = 'block';
    audioPlayer.style.display = 'none';

    const statusText = document.getElementById('statusText');
    const progressFill = document.getElementById('progressFill');

    statusText.textContent = 'Processing audio...';
    progressFill.style.width = '0%';

    // Simulate progress
    let progress = 0;
    const interval = setInterval(() => {
        progress += 5;
        progressFill.style.width = progress + '%';

        if (progress >= 95) {
            clearInterval(interval);
        }
    }, 500);

    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                youtube_url: youtubeUrlToProcess,
                enhanced: enhancedMode.checked
            })
        });

        const data = await response.json();

        clearInterval(interval);
        progressFill.style.width = '100%';

        if (data.error) {
            alert('Processing failed: ' + data.error);
            processingStatus.style.display = 'none';
            outputPlaceholder.style.display = 'flex';
            return;
        }

        setTimeout(() => {
            processingStatus.style.display = 'none';
            audioPlayer.style.display = 'block';
            document.getElementById('songTitle').textContent = data.title || 'Processed Song';
            document.getElementById('audioSource').src = data.audio_path;
            document.getElementById('audioElement').load();
        }, 500);

    } catch (error) {
        clearInterval(interval);
        console.error('Processing error:', error);
        alert('Processing failed: ' + error.message);
        processingStatus.style.display = 'none';
        outputPlaceholder.style.display = 'flex';
    }
});

// System panel toggle
const panelToggle = document.getElementById('panelToggle');
const systemPanel = document.getElementById('systemPanel');

panelToggle.addEventListener('click', () => {
    systemPanel.classList.toggle('collapsed');
});

// Load system info
async function loadSystemInfo() {
    try {
        const response = await fetch('/api/system-info');
        const data = await response.json();

        document.querySelector('.stat-card:nth-child(1) .stat-value').textContent = data.yt_dlp;
        document.querySelector('.stat-card:nth-child(2) .stat-value').textContent = data.ffmpeg;
        document.querySelector('.stat-card:nth-child(3) .stat-value').textContent = data.models;
        document.querySelector('.stat-card:nth-child(4) .stat-value').textContent = data.cached_files;
    } catch (error) {
        console.error('Failed to load system info:', error);
    }
}

loadSystemInfo();

// Clear cache
const clearCache = document.getElementById('clearCache');
const cacheCount = document.getElementById('cacheCount');

clearCache.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/clear-cache', {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            cacheCount.textContent = '0';
            alert('Cache cleared successfully!');
            loadSystemInfo();
        }
    } catch (error) {
        alert('Failed to clear cache: ' + error.message);
    }
});

// Download button
const downloadBtn = document.getElementById('downloadBtn');

downloadBtn.addEventListener('click', () => {
    const audioSrc = document.getElementById('audioSource').src;
    if (audioSrc) {
        const link = document.createElement('a');
        link.href = audioSrc;
        link.download = document.getElementById('songTitle').textContent + '.mp3';
        link.click();
    }
});
