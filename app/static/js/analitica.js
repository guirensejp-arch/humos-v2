/* Gráficos de Analítica. Lee los datos embebidos en #analitica-datos y usa
   Chart.js (CDN). Si Chart.js no cargó, la página sigue funcionando con KPIs
   y tablas: el script sale sin hacer nada. */
(function () {
  'use strict';

  var contenedor = document.getElementById('analitica-datos');
  if (!contenedor || !window.Chart) {
    return;
  }

  var datos;
  try {
    datos = JSON.parse(contenedor.textContent);
  } catch (error) {
    return;
  }

  var estilos = getComputedStyle(document.documentElement);
  function color(nombre, respaldo) {
    var valor = (estilos.getPropertyValue(nombre) || '').trim();
    return valor || respaldo;
  }

  var primario = color('--color-primario', '#1C1815');
  var secundario = color('--color-secundario', '#DB423C');
  var acento = color('--color-acento', '#A62B23');
  var paleta = [secundario, acento, primario, '#F2B84B', '#4CAF7D', '#7E8BA3', '#C96BD6'];

  function conAlfa(hex, alfa) {
    return /^#[0-9a-fA-F]{6}$/.test(hex) ? hex + alfa : hex;
  }

  var formatoMoneda = new Intl.NumberFormat('es-AR', {
    style: 'currency', currency: 'ARS', maximumFractionDigits: 0,
  });
  var formatoNumero = new Intl.NumberFormat('es-AR');

  function moneda(centavos) {
    return formatoMoneda.format((centavos || 0) / 100);
  }

  function numero(valor) {
    return formatoNumero.format(valor || 0);
  }

  function crear(id, configuracion) {
    var canvas = document.getElementById(id);
    if (!canvas) {
      return;
    }
    new Chart(canvas, configuracion);
  }

  var ejesMoneda = {
    y: { ticks: { callback: function (valor) { return moneda(valor); } } },
  };
  var tooltipMoneda = {
    callbacks: {
      label: function (contexto) {
        return (contexto.dataset.label || '') + ': ' + moneda(contexto.parsed.y);
      },
    },
  };

  crear('graficoVentas', {
    type: 'line',
    data: {
      labels: datos.serie.labels,
      datasets: [{
        label: 'Ventas',
        data: datos.serie.ventas,
        borderColor: secundario,
        backgroundColor: conAlfa(secundario, '22'),
        fill: true,
        tension: 0.3,
        pointRadius: 2,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false }, tooltip: tooltipMoneda },
      scales: ejesMoneda,
    },
  });

  crear('graficoPedidos', {
    type: 'bar',
    data: {
      labels: datos.serie.labels,
      datasets: [{
        label: 'Pedidos',
        data: datos.serie.pedidos,
        backgroundColor: primario,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function (contexto) {
              return numero(contexto.parsed.y) + ' pedidos';
            },
          },
        },
      },
    },
  });

  crear('graficoTicket', {
    type: 'line',
    data: {
      labels: datos.serie.labels,
      datasets: [{
        label: 'Ticket promedio',
        data: datos.serie.ticket,
        borderColor: acento,
        backgroundColor: conAlfa(acento, '22'),
        fill: true,
        tension: 0.3,
        pointRadius: 2,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false }, tooltip: tooltipMoneda },
      scales: ejesMoneda,
    },
  });

  function tarta(id, bloque) {
    crear(id, {
      type: 'doughnut',
      data: {
        labels: bloque.labels,
        datasets: [{ data: bloque.valores, backgroundColor: paleta, borderWidth: 1 }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: {
              label: function (contexto) {
                return contexto.label + ': ' + moneda(contexto.parsed);
              },
            },
          },
        },
      },
    });
  }

  tarta('graficoMetodos', datos.metodos);
  tarta('graficoOrigenes', datos.origenes);
  tarta('graficoEntregas', datos.entregas);

  function barraHorizontal(id, bloque, etiqueta, formateador) {
    crear(id, {
      type: 'bar',
      data: {
        labels: bloque.labels,
        datasets: [{
          label: etiqueta,
          data: bloque.valores,
          backgroundColor: secundario,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (contexto) {
                return etiqueta + ': ' + formateador(contexto.parsed.x);
              },
            },
          },
        },
        scales: {
          x: { ticks: { callback: function (valor) { return formateador(valor); } } },
        },
      },
    });
  }

  barraHorizontal('graficoTopUnidades', datos.top_unidades, 'Unidades', numero);
  barraHorizontal('graficoTopFacturacion', datos.top_facturacion, 'Facturación', moneda);
})();
