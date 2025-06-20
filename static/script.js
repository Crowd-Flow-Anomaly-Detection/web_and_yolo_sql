function changeMonth(offset) {
    var currentYear = parseInt(document.querySelector('h1').innerText.split('年')[0]);
    var currentMonth = parseInt(document.querySelector('h1').innerText.split('年')[1].split('月')[0]);
    var newMonth = currentMonth + offset;

    if (newMonth < 1) {
        newMonth = 12;
        currentYear -= 1;
    } else if (newMonth > 12) {
        newMonth = 1;
        currentYear += 1;
    }

    window.location.href = `/?year=${currentYear}&month=${newMonth}`;
}

function showFootfall(year, month, day) {
    const img = document.getElementById('footfallChart');
    img.src = `/footfall_chart/${year}/${month}/${day}.png`;
    img.style.display = 'block';

    fetch(`/api/footfall/${year}/${month}/${day}`)
        .then(response => response.json())
        .then(data => {
            const detailsDiv = document.getElementById('footfall-details');
            detailsDiv.innerHTML = `<h2>${year}-${month}-${day} 人流資料</h2>`;
            if (data.error) {
                detailsDiv.innerHTML += `<p>${data.error}</p>`;
                img.style.display = 'none';
            } else {
                detailsDiv.innerHTML += `<p>總人流量: ${data.footfall.reduce((a, b) => a + b, 0)}</p>`;
            }
            detailsDiv.style.display = 'block'; // 顯示原本隱藏的人流資料
        })
        .catch(error => {
            console.error('Error fetching footfall data:', error);
        });
}

document.getElementById('uploadBtn').addEventListener('click', () => {
  const fileInput = document.getElementById('videoInput');
  if (!fileInput.files || fileInput.files.length === 0) {
    alert('請先選擇要上傳的影片');
    return;
  }

  // 1. 準備 FormData
  const formData = new FormData();
  formData.append('video', fileInput.files[0]);

  // 2. POST 到後端
  fetch('/api/upload_video', {
    method: 'POST',
    body: formData
  })
  .then(res => {
    if (!res.ok) throw new Error('上傳失敗: ' + res.status);
    return res.json();
  })
  .then(data => {
    // 後端 JSON 應該長這樣：
    // { message, file_path, footfall, download_url }
    const url = data.download_url;
    if (!url) {
      alert('後端沒有回傳 download_url');
      return;
    }

    // 3. 指定給 video，並顯示／播放
    const player = document.getElementById('videoPlayer');
    player.src = url;           // e.g. "/api/download_video/count_footfall/output/highway.mp4"
    player.style.display = 'block';
    player.load();              // 重新載入新的 src
    player.play().catch(()=>{}); // 自動播放（部分瀏覽器可能需要 user gesture）
  })
  .catch(err => {
    console.error(err);
    alert('發生錯誤，請看 console');
  });
});


