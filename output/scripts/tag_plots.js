plotTagHeatmap = function (coocs, id) {
    Highcharts.chart(id, {
        chart: {
            type: 'heatmap',
            height: '100%',
            zoomType: 'xy'
        },
        title: {
            text: 'Correlation between tags',
            align: 'left'
        },

        subtitle: {
            text: 'Rows and columns correspond to tags, while color shows their correlation',
            align: 'left'
        },
        xAxis: {
            gridLineWidth: 0,
            categories: coocs.tags,
            title: null
        },
        yAxis: {
            gridLineWidth: 0,
            categories: coocs.tags,
            title: null
        },
        colorAxis: {
            min: 0,
            max: 1,
            minColor: '#FFFFFF',
            maxColor: Highcharts.getOptions().colors[0]
        },
        series: [{
            data: coocs.freqs.ti1.map((d, i) => [d, coocs.freqs.ti2[i], coocs.freqs.cooc[i]]),
        }],
        tooltip: {
            formatter() {
                return `Tag 1: <b>${this.series.xAxis.categories[this.point.x]}</b><br>` +
                       `Tag 2: <b>${this.series.yAxis.categories[this.point.y]}</b><br>` +
                       `Correlation: <b>${Math.round(this.point.value * 1000) / 1000}</b>`;
            }
        },
        credits: {enabled: false}
    });
}

document.addEventListener("DOMContentLoaded", function() {
    fetch('data/tag_info.json').then(res => res.json()).then(data => {
        const n_docs = data.n_docs;
        const coocs = data.coocs;
        plotTagHeatmap(coocs, 'tag-heatmap');
        Highcharts.chart('n-docs-per-tag', {
            plotOptions: {
                histogram: {
                    binsNumber: 200
                }
            },
            chart: {
                zoomType: 'x'
            },
            title: {text: 'Number of documents per tag'},
            xAxis: {
                title: {text: 'Number of documents per tag'},
            },
            yAxis: {
                type: 'logarithmic',
                title: {text: 'Number of tags'}
            },
            legend:{ enabled:false },
            credits: {enabled: false},
            series: [
                {
                    type: 'histogram',
                    baseSeries: 'hbase',
                },
                {
                    data: n_docs,
                    id: 'hbase',
                    visible: false
                }
            ],
            tooltip: {
                formatter() {
                    return `Number of documents: <b>${Math.ceil(this.point.x)} - ${Math.floor(this.point.x2)}</b><br>` +
                            `Number of tags: <b>${this.y}</b>`;
                }
            }
        })

        const cum_fracs = data.cum_fracs;
        // sum of a vectore
        const total_n_docs = data.n_docs_total;
        Highcharts.chart('frac-docs-per-tag', {
            chart: {
                zoomType: 'x'
            },
            title: {text: 'Number of tags per number of documents'},
            xAxis: {
                type: 'logarithmic',
                title: {text: 'Number of documents per tag'}
            },
            yAxis: {
                title: {text: 'Fraction of tags with less than this number of documents'},
                max: 1
            },
            legend:{ enabled:false },
            credits: {enabled: false},
            series: [{
                // data: cum_fracs.fracs,
                data: cum_fracs.fracs.map((d, i) => ({x: cum_fracs.n_docs[i], y: d})),
            }],
            tooltip: {
                formatter() {
                    return `Number of documents: <b>${Math.ceil(this.point.x)}</b><br>` +
                            `Fraction of tags: <b>${Math.round(this.point.y * 1000) / 1000}</b><br>` +
                            `Number of tags: <b>${Math.round(this.point.y * data.n_tags_total)}</b><br>` +
                            `Fraction of documents: <b>${Math.round(this.point.x / total_n_docs * 10000) / 10000}</b>`;
                }
            }
        })

        const n_tags = data.n_tags;
        Highcharts.chart('n-tags-per-doc', {
            chart: {
                type: 'column',
                zoomType: 'x'
            },
            title: {text: 'Number of tags per document'},
            xAxis: {
                title: {text: 'Number of tags per document'},
            },
            yAxis: {
                title: {text: 'Number of documents'}
            },
            legend:{ enabled:false },
            credits: {enabled: false},
            series: [{
                data: n_tags.n_tags.map((n, i) => [n, n_tags.count[i]]),
            }],
            tooltip: {
                formatter() {
                    return `Number of tags: <b>${this.point.x}</b><br>` +
                            `Number of documents: <b>${this.point.y}</b>`;
                }
            }
        })

        const tags = data.tag_embedding;
        Highcharts.chart('tag-scatter', {
            title: {text: 'Tag embedding'},
            xAxis: {
                title: {text: 'Dimension 1'},
                labels: {enabled: false},
                tickLength: 0,
                lineWidth: 1,
                gridLineWidth: 1
            },
            yAxis: {
                title: {text: 'Dimension 2'},
                labels: {enabled: false},
                tickLength: 0,
                lineWidth: 1,
                gridLineWidth: 1
            },
            chart: {
                type: 'bubble',
                height: '100%',
                zoomType: 'xy',
            },
            plotOptions: {
                bubble: {
                    maxSize: '5%'
                }
            },
            series: [{
                dataLabels: {
                    enabled: true,
                    format: '{point.tag}',
                    style: {
                        'fontSize': '7px'
                    }
                },
                data: tags.map(d => {return {'x': d.x, 'y': d.y, 'z': Math.log(d.n_docs), 'tag': d.tag, 'n_docs': d.n_docs};})
            }],
            tooltip: {
                formatter() {
                    return `<b>${this.point.tag}</b> <br> Num. docs: <b>${this.point.n_docs}</b>`
                }
            },
            credits: {enabled: false},
            legend: {enabled: false}
        });

        const coocs_filt = data.coocs_filt;
        plotTagHeatmap(coocs_filt, 'tag-heatmap-filt');
    });
});