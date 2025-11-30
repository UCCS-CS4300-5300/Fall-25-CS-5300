/*JavaScript for results charts
After a user completes their mock interview they will be given a page of their results 
*/

const inputData = JSON.parse(document.getElementById('chart-data').textContent);

// Get CSS theme variables
const styles = getComputedStyle(document.documentElement);
const textPrimaryColor = styles.getPropertyValue('--text-primary').trim();
const primaryColor = styles.getPropertyValue('--primary').trim();
const primaryLightColor = styles.getPropertyValue('--primary-light').trim();
const accentColor = styles.getPropertyValue('--accent').trim();
const successColor = styles.getPropertyValue('--success').trim();

//Bar Graph - Use CSS variables for theme compatibility
const barColors = [primaryColor, primaryLightColor, accentColor, successColor];

Chart.defaults.backgroundColor = primaryLightColor;
Chart.defaults.borderColor = primaryColor;
Chart.defaults.color = textPrimaryColor;

const BarChart = document.getElementById('BarChart').getContext('2d');
const chart1 = new Chart(BarChart, {
    type: "bar",
    data: {
      labels: Object.keys(inputData),
      datasets: [{
        backgroundColor: barColors,
        data: Object.values(inputData),
      }]
    },
    options: {
        legend: {
          display: false,
        },
        title: {
          display: true,
          text: "Category scores (out of 100)",
          fontColor: textPrimaryColor,
          fontFamily: "Verdana, Geneva, Tahoma, sans-serif",
          fontSize: 16,
        },
        scales: {
          yAxes: [{
            ticks: {
              beginAtZero: true,
              min: 0,
              max: 100,
              stepSize: 20,
              fontColor: textPrimaryColor,
              fontFamily: "Verdana, Geneva, Tahoma, sans-serif",
            },
            gridLines: {
              color: 'rgba(128, 128, 128, 0.2)',
            }
          }],
          xAxes: [{
            ticks: {
              fontColor: textPrimaryColor,
              fontFamily: "Verdana, Geneva, Tahoma, sans-serif",
            },
            gridLines: {
              color: 'rgba(128, 128, 128, 0.2)',
            }
          }]
      }
    }
  });






  
const DonutChart = document.getElementById("DonutChart").getContext('2d');
DonutChart.width =2000;
DonutChart.height = 2000;
const chart2 = new Chart(DonutChart, {
  type: 'doughnut',

  data: {
    labels: Object.keys(inputData),
    datasets: [{
      data: Object.values(inputData),
      backgroundColor: barColors,
      hoverOffset: 4
    }],
  },
  options: {
    title:{
      display: true,
      text: 'Categories',
      fontColor: textPrimaryColor,
      fontFamily: "Verdana, Geneva, Tahoma, sans-serif",
      fontSize: 16,
    },
    legend: {
      labels: {
        fontColor: textPrimaryColor,
        fontFamily: "Verdana, Geneva, Tahoma, sans-serif",
      }
    },
  },
});

