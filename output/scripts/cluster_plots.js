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
  fetch('data/clust_info.json').then(res => res.json()).then(data => {
      const coocs = data.tag_coocs;
      const bar_info = data.bar_info;

      Highcharts.chart('cluster-heatmap', Highcharts.merge(heatmapOptions, {
          chart: {
              height: '900px',
          },
          title: {
              text: 'Specificity of tags to clusters',
              align: 'left'
          },

          subtitle: {
              text: 'Rows correspond to tags, columns correspond to clusters, and color shows specificity of tags to clusters',
              align: 'left'
          },
          xAxis: {
              categories: coocs.clust_levels,
          },
          yAxis: {
              categories: coocs.tag_levels,
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
      }));

      ['posts', 'tags'].forEach(p => {
          Highcharts.chart(`n-${p}-per-cluster-bar`, Highcharts.merge(barOptions, {
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
              colorAxis: {},
              plotOptions: {
                  column: {
                      dataLabels: {
                          enabled: true
                      }
                  }
              },
              legend: { enabled:false },
              series: [{name: `Num. of ${p}`, data: bar_info[`num_${p}`], type: 'column'}],
          }));
      })

      const cids = ['n-posts-per-cluster-bar', 'n-tags-per-cluster-bar'];
      cids.forEach(id => {
          document.getElementById(id).addEventListener('mousemove', syncTooltip);
          document.getElementById(id).addEventListener('mouseout', mouseOutDetected);
      });
  })

  fetch('data/user_clust_matching.json').then(res => res.json()).then(data => {
    const hm_info = data;
    Highcharts.chart('cluster-user-heatmap', Highcharts.merge(heatmapOptions, {
        chart: {
            height: '900px',
        },
        title: {
            text: 'Specificity of users to clusters',
            align: 'left'
        },

        subtitle: {
            text: 'Rows correspond to users, columns correspond to clusters, and color shows specificity of users to clusters',
            align: 'left'
        },
        xAxis: {
            categories: hm_info.clust_levels,
        },
        yAxis: {
            labels: {enabled: false},
            title: {text: "Users"},
        },
        series: [{
            data: hm_info.scores.user.map((t,i) => [hm_info.scores.cluster[i], t, hm_info.scores.score[i]]),
        }],
        tooltip: {
            formatter: function () {
                return `Cluster: <b>${this.series.xAxis.categories[this.point.x]}</b><br>` +
                       `User: <b>${hm_info.usernames[this.point.y]}</b><br>` +
                       `Score: <b>${this.point.value}</b><br>`;
            }
        },
        credits: {enabled: false}
    }));
  })
});