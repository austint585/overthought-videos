// Records the reel playing in the current Instagram tab and saves it to ~/Downloads, for pipeline/watch.py.
// Run it with the Claude in Chrome javascript tool on an open reel page (https://www.instagram.com/reel/<code>/).
// Set NAME first; it records in real time (the reel's length), so check window.__rec until state is "done".
const NAME = window.__reelName || 'reel';
const v = [...document.querySelectorAll('video')].find(x => !x.paused) || document.querySelector('video');
v.currentTime = 0;
const stream = v.captureStream();
const chunks = [];
const rec = new MediaRecorder(stream, {mimeType: 'video/webm;codecs=vp8,opus'});
rec.ondataavailable = e => e.data.size && chunks.push(e.data);
window.__rec = {state: 'recording', size: 0, seconds: v.duration};
rec.onstop = () => {
  const blob = new Blob(chunks, {type: 'video/webm'});
  window.__rec.size = blob.size;
  window.__rec.state = 'done';
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'overthought_reel_' + NAME + '.webm';
  document.body.appendChild(a); a.click(); a.remove();
};
rec.start(1000);
v.play();
setTimeout(() => rec.stop(), Math.ceil((v.duration + 0.5) * 1000));
window.__rec
