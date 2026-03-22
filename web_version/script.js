const videoElement = document.getElementsByClassName('input_video')[0];
const canvasElement = document.getElementsByClassName('output_canvas')[0];
const canvasCtx = canvasElement.getContext('2d');
const volFill = document.getElementById('vol-fill');
const volValue = document.getElementById('vol-value');
const loading = document.getElementById('loading');

let lastVolume = 0;

function onResults(results) {
  loading.style.display = 'none';
  
  // Clear canvas
  canvasCtx.save();
  canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
  canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);
  
  if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
    for (const landmarks of results.multiHandLandmarks) {
      // Draw landmarks
      drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {color: '#00FF00', lineWidth: 5});
      drawLandmarks(canvasCtx, landmarks, {color: '#FF0000', lineWidth: 2});
      
      // Volume Logic: Normalized Relative movement (Index Tip vs Wrist)
      const wrist = landmarks[0];
      const index = landmarks[8];
      const palmBase = landmarks[9]; // Middle MCP
      
      // Calculate palm size for normalization
      const palmSize = Math.sqrt(
        Math.pow(palmBase.x - wrist.x, 2) + 
        Math.pow(palmBase.y - wrist.y, 2)
      );
      
      if (palmSize > 0) {
        // Normalize the vertical distance
        const relativeY = (wrist.y - index.y) / palmSize;
        
        // Map relativeY (approx 0.8 to 1.8) to 0-100
        let vol = Math.round((relativeY - 0.8) / 1.0 * 100);
        vol = Math.max(0, Math.min(100, vol));
        
        // Update UI
        volFill.style.width = vol + '%';
        volValue.innerText = vol + '%';
      }
      
      // Visual feedback
      const x = index.x * canvasElement.width;
      const y = index.y * canvasElement.height;
      const wx = wrist.x * canvasElement.width;
      const wy = wrist.y * canvasElement.height;
      
      canvasCtx.beginPath();
      canvasCtx.moveTo(wx, wy);
      canvasCtx.lineTo(x, y);
      canvasCtx.strokeStyle = '#0078d7';
      canvasCtx.lineWidth = 3;
      canvasCtx.stroke();
      
      canvasCtx.beginPath();
      canvasCtx.arc(x, y, 15, 0, 2 * Math.PI);
      canvasCtx.fillStyle = '#0078d7';
      canvasCtx.fill();
    }
  }
  canvasCtx.restore();
}

const hands = new Hands({
  locateFile: (file) => {
    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
  }
});

hands.setOptions({
  maxNumHands: 1,
  modelComplexity: 1,
  minDetectionConfidence: 0.3,
  minTrackingConfidence: 0.3
});

hands.onResults(onResults);

const camera = new Camera(videoElement, {
  onFrame: async () => {
    await hands.send({image: videoElement});
  },
  width: 640,
  height: 480
});

camera.start();

// Handle responsive canvas
function resize() {
  canvasElement.width = videoElement.videoWidth || 640;
  canvasElement.height = videoElement.videoHeight || 480;
}

videoElement.addEventListener('loadedmetadata', resize);
window.addEventListener('resize', resize);
