<template>
  <div id="app-container">
    <h1>Aplicativo de Desenho Colaborativo</h1>
    <DrawingCanvas />
  </div>
</template>

<script setup>
import DrawingCanvas from './components/DrawingCanvas.vue';
</script>

<style>
/* Estilos globais ou para App.vue */
body {
  font-family: sans-serif;
  margin: 0;
  background-color: #f0f0f0;
  display: flex;
  justify-content: center;
  align-items: flex-start; /* Alinha no topo se o conteúdo for menor que a tela */
  min-height: 100vh;
  padding-top: 20px; /* Espaço no topo */
}

#app-container {
  text-align: center;
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

h1 {
  color: #333;
}
</style>