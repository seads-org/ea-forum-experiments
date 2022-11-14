function mouseOutDetected() {
    var i, chart;
    for (i = 1; i < Highcharts.charts.length; i = i + 1) {
      chart = Highcharts.charts[i];
      chart.tooltip.hide();
      chart.series.forEach(series => {
          series.points.forEach(point => {
          point.setState();
        });
      });
    }
}

function syncTooltip(e) {
    var chart, point, i, event;

    for (i = 1; i < Highcharts.charts.length; i = i + 1) {
      chart = Highcharts.charts[i];
      // Find coordinates within the chart
      event = chart.pointer.normalize(e);
      // Get the hovered point
      const points = chart.series.reduce((points, series, seriesInx) => {
        const point = series.searchPoint(event, true);
        if (point)
          points.push(point);
        return points;
      }, []);

      chart.series.forEach(series => {
          chart.series.forEach(point => {
          point.setState();
        });
      });

      chart.series.forEach(point => {
        point.setState('hover'); // show hover marker
      });

      if (points.length > 0)
        chart.tooltip.refresh(points);

    }
}

document.addEventListener('DOMContentLoaded', function () {
  fetch('http://localhost:8000/clust_info.json').then(res => res.json()).then(data => {
      const coocs = data.tag_coocs;
      const bar_info = data.bar_info;

      Highcharts.chart('cluster-heatmap', {
          chart: {
              type: 'heatmap',
              height: '900px',
              zoomType: 'xy'
          },
          title: {
              text: 'Specificity of tags to clusters',
              align: 'left'
          },

          subtitle: {
              text: 'Rows and correspond to tags, columns correspond to clusters, and color shows specificity of tags to clusters',
              align: 'left'
          },
          xAxis: {
              categories: coocs.clust_levels,
              title: null
          },
          yAxis: {
              categories: coocs.tag_levels,
              title: null
          },
          colorAxis: {
              min: 0,
              max: 1,
              minColor: '#FFFFFF',
              maxColor: Highcharts.getOptions().colors[0]
          },
          series: [{
              data: coocs.coocs.map(d => [d.clust, d.tag, d.score]),
          }],
          tooltip: {
              formatter: function () {
                  return `Cluster: <b>${this.series.xAxis.categories[this.point.x]}</b><br>` +
                         `Tag: <b>${this.series.yAxis.categories[this.point.y]}</b><br>` +
                         `Score: <b>${this.point.value}</b><br>`;
              }
          },
          credits: {enabled: false}
      });

      ['posts', 'tags'].forEach(p => {
          Highcharts.chart(`n-${p}-per-cluster-bar`, {
              chart: {
                  type: 'column'
              },
              title: {
                  text: `Number of ${p} per cluster`
              },
              xAxis: {
                  categories: bar_info.clusters,
                  title: {text: null}
              },
              yAxis: {
                  min: 0,
                  title: {text: `Num. ${p}`},
                  labels: {
                      overflow: 'justify'
                  }
              },
              plotOptions: {
                  column: {
                      dataLabels: {
                          enabled: true
                      }
                  }
              },
              legend: { enabled:false },
              series: [{'name': `Num. of ${p}`, 'data': bar_info[`num_${p}`]}],
              credits: {enabled: false}
          });
      })

      const cids = ['n-posts-per-cluster-bar', 'n-tags-per-cluster-bar'];
      cids.forEach(id => {
          document.getElementById(id).addEventListener('mousemove', syncTooltip);
          document.getElementById(id).addEventListener('mouseout', mouseOutDetected);
      });
  })
});