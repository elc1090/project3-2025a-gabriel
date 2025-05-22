<template>
  <canvas
    ref="canvasRef"
    @mousedown="startDrawing"
    @mousemove="draw"
    @mouseup="stopDrawing"
    @mouseout="stopDrawing"
    @touchstart.prevent="startDrawingTouch"
    @touchmove.prevent="drawTouch"
    @touchend="stopDrawingTouch"
    class="drawing-canvas"
  ></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const canvasRef = ref(null); // Referência para o elemento canvas
let ctx = null; // Contexto 2D do canvas
let isDrawing = false;
let lastX = 0;
let lastY = 0;

// Configurações do desenho
const drawColor = 'black';
const lineWidth = 3;

onMounted(() => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  // Ajustar o tamanho do canvas para preencher o contêiner ou ter um tamanho fixo
  // Para este exemplo, vamos usar um tamanho fixo.
  // Idealmente, você faria isso de forma responsiva.
  canvas.width = 800; // ou window.innerWidth * 0.8
  canvas.height = 600; // ou window.innerHeight * 0.7

  ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.lineCap = 'round'; // Pontas das linhas arredondadas
  ctx.lineJoin = 'round'; // Junções das linhas arredondadas
  ctx.strokeStyle = drawColor;
  ctx.lineWidth = lineWidth;

  // Opcional: Adicionar um listener para redimensionamento da janela
  // window.addEventListener('resize', resizeCanvas);
  // resizeCanvas(); // Chamar uma vez para definir o tamanho inicial
});

// onUnmounted(() => {
//   window.removeEventListener('resize', resizeCanvas);
// });

// Função para ajustar o tamanho do canvas (opcional e mais avançado para responsividade)
// function resizeCanvas() {
//   const canvas = canvasRef.value;
//   if (canvas && canvas.parentElement) {
//     canvas.width = canvas.parentElement.clientWidth;
//     canvas.height = canvas.parentElement.clientHeight;
//     // Redefinir propriedades do contexto se necessário após redimensionar
//     if (ctx) {
//       ctx.lineCap = 'round';
//       ctx.lineJoin = 'round';
//       ctx.strokeStyle = drawColor;
//       ctx.lineWidth = lineWidth;
//     }
//   }
// }

// --- Funções de Desenho para Mouse ---
function startDrawing(event) {
  if (!ctx) return;
  isDrawing = true;
  [lastX, lastY] = [event.offsetX, event.offsetY];
}

function draw(event) {
  if (!isDrawing || !ctx) return;
  const currentX = event.offsetX;
  const currentY = event.offsetY;

  ctx.beginPath();
  ctx.moveTo(lastX, lastY);
  ctx.lineTo(currentX, currentY);
  ctx.stroke();

  [lastX, lastY] = [currentX, currentY];
}

function stopDrawing() {
  isDrawing = false;
}

// --- Funções de Desenho para Toque ---
function startDrawingTouch(event) {
  if (!ctx || event.touches.length === 0) return;
  isDrawing = true;
  const touch = event.touches[0];
  const rect = canvasRef.value.getBoundingClientRect();
  [lastX, lastY] = [touch.clientX - rect.left, touch.clientY - rect.top];
}

function drawTouch(event) {
  if (!isDrawing || !ctx || event.touches.length === 0) return;
  const touch = event.touches[0];
  const rect = canvasRef.value.getBoundingClientRect();
  const currentX = touch.clientX - rect.left;
  const currentY = touch.clientY - rect.top;

  ctx.beginPath();
  ctx.moveTo(lastX, lastY);
  ctx.lineTo(currentX, currentY);
  ctx.stroke();

  [lastX, lastY] = [currentX, currentY];
}

function stopDrawingTouch() {
  isDrawing = false;
}

</script>

<style scoped>
.drawing-canvas {
  border: 1px solid #ccc;
  cursor: crosshair;
  /* Para garantir que o tamanho definido no JS seja respeitado
     e o canvas não seja esticado/encolhido pelo CSS de forma inadequada. */
  display: block; /* Remove espaço extra abaixo do canvas (inline) */
  margin: 20px auto; /* Centraliza e adiciona margem */
}
</style>