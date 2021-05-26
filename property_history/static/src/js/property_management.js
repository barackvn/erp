odoo.define('property_history.action_export', function(require) {
  "use strict";
  var core = require('web.core');
  var Widget = require('web.Widget');
  var Model = require('web.Model');
  var session = require('web.session');
  var PlannerCommon = require('web.planner.common');
  var framework = require('web.framework');
  var webclient = require('web.web_client');
  var AccountAnalytic = new Model('account.analytic.account');
  var PropertyHistory = new Model('property.history');
  var QWeb = core.qweb;
  var _t = core._t;

  var PropertyHistoryDashboard = Widget.extend({
    template: 'PropertyHistoryDashboard',
    events: {
      'change .date_filter': '_change_date_to',
      'click .df_selection_text': '_change_ks_date_selector',
    },
    init: function(parent, data) {
      this.dashboards_templates = ['PosOrders'];
      this.payment_details = [];
      this.top_salesperson = [];
      this.selling_product = [];
      this.total_sale = [];
      this.total_order_count = [];
      this.total_refund_count = [];
      this.total_session = [];
      this.today_refund_total = [];
      this.today_sale = [];
      this.categories = [];
      return this._super.apply(this, arguments);
    },
    start: function() {
      var self = this;
      this.set("title", 'Dashboard');
      return this._super().then(function() {
        self.render_dashboards();
        self.render_graphs();
        self.$el.parent().addClass('oe_background_grey');
      });
    },
    _change_ks_date_selector: function(event){
      var self = this
      var evento = $(event.currentTarget)
      var typedate = evento.attr('id')
      var date_to = $('#date_to').val()
      var date_from = $('#date_from').val()
      if (typedate == 'month'){
        $('#month').attr('focus', '1')
        $('#year').attr('focus', '0')
      }else{
        $('#month').attr('focus', '0')
        $('#year').attr('focus', '1')
      }
      self.render_top_product_graph(typedate,date_to,date_from)
      self.render_available_meters(typedate,date_to,date_from)
    },
    _change_date_to: function(event){
      var self = this
      var evento = $(event.currentTarget)
      var span_date = $(".df_selection_text[focus='1']")
      var typedate = span_date.attr('id')
      var date_to = $('#date_to').val()
      var date_from = $('#date_from').val()
      self.render_top_product_graph(typedate,date_to,date_from)
      self.render_available_meters(typedate,date_to,date_from)
    },
    render_dashboards: function() {
      var self = this;
      var today = new Date();
      var date_to = today.toISOString().substr(0, 10)
      _.each(this.dashboards_templates, function(template) {
        self.$('.o_property_dashboard').append(QWeb.render(template, {
          widget: self,
          date_to: date_to,
        }));
      });
    },
    render_graphs: function() {
      var self = this;
      self.render_top_product_graph();
      self.render_available_meters();
    },
    render_top_product_graph: function(datetype='month',date_to,date_from) {
      console.log('render_top_product_graph')
      console.log(datetype)
      console.log(date_to)
      console.log(date_from)
      var self = this
      var ctx = self.$(".top_selling_product")
      PropertyHistory.call("get_the_top_products", [datetype,date_to,date_from]).then(function(arrays) {
        $('#lineChart').replaceWith($('<canvas id="lineChart"  class="top_selling_product" width="800" height="450"></canvas>'));
        var data = {
          labels: arrays[1],
          datasets: [{
              label: "Ventas",
              data: arrays[0],
              borderColor: 'rgba(255, 0, 0, 0.5)',
              backgroundColor: 'rgb(255,0,0,0.1)',
            },
          ]
        };
        //options
        var options = {
          responsive: true,
          backgroundColor: 'rgb(255,0,0)',
          borderColor: 'rgb(255,0,0)',
          title: {
            display: true,
            position: "top",
            text: "Total de ventas",
            fontSize: 18,
            fontColor: "#111"
          },
          legend: {
            display: false,
            position: "bottom",
            labels: {
              fontColor: "#333",
              fontSize: 16
            }
          },
          scales: {
            xAxes: [{
              ticks: {
                min: 0
              },
              scaleLabel: {
                display: true,
                labelString: 'Fecha de renta'
              }
            }],
          }
        };
        //create Chart class object
        new Chart(document.getElementById("lineChart"), {
          type: "line",
          data: data,
          options: options
        });
      });
    },

    render_available_meters: function(datetype='month',date_to,date_from) {
      console.log('render_available_meters')
      console.log(datetype)
      console.log(date_to)
      console.log(date_from)
      var self = this
      var ctx = self.$(".render_available_meters_ctx")[0].getContext('2d')
      AccountAnalytic.call("get_the_available_meters", [datetype,date_to,date_from]).then(function(arrays) {
        $('#barChart').replaceWith($('<canvas id="barChart" class="render_available_meters_ctx" width="800" height="450"></canvas>'));
        var data = {
          labels: arrays[1],
          datasets: [
            {
              label: "Espacio Total",
              data: arrays[0],
              borderColor: '#9ad0f5',
              backgroundColor: '#9ad0f5',
            },
            {
              label: "Espacio Ocupado",
              data: arrays[2],
              borderColor: '#ffe6aa',
              backgroundColor: '#ffe6aa',
            },
          ]
        };
        //options
        var options = {
          responsive: true,
          backgroundColor: '#dbf3f3',
          borderColor: '#4bc0c0',
          title: {
            display: true,
            position: "top",
            text: "Espacio total - Espacio ocupado en m2",
            fontSize: 18,
            fontColor: "#111"
          },
          legend: {
            position: "bottom",
            labels: {
              fontColor: "#333",
            }
          },
          scales: {
            xAxes: [{
              ticks: {
                min: 0
              },
              scaleLabel: {
                display: true,
                labelString: 'Fecha'
              }
            }],
            yAxes: [{
              ticks: {
                min: 0
              },
              scaleLabel: {
                display: true,
                labelString: 'Metros cuadrados'
              }
            }],
          }
        };
        //create Chart class object

       new Chart(document.getElementById("barChart"), {
          type: "bar",
          data: data,
          options: options
        });
      });
    },

  });

  core.action_registry.add('property_history_dashboard', PropertyHistoryDashboard);

  return PropertyHistoryDashboard;



})
