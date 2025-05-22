<template>
  <div id="app-container">
    <DrawingCanvas />
  </div>
</template>

<script setup>
import DrawingCanvas from './components/DrawingCanvas.vue';
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  overflow: hidden; /* Para evitar barras de rolagem da página */
  background-color: #333; /* Cor de fundo escura para a página */
}

#app-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
}
</style>