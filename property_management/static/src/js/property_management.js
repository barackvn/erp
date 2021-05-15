odoo.define('property_management.action_export', function(require) {
  "use strict";
  var core = require('web.core');
  var Widget = require('web.Widget');
  var Model = require('web.Model');
  var session = require('web.session');
  var PlannerCommon = require('web.planner.common');
  var framework = require('web.framework');
  var webclient = require('web.web_client');
  var AccountAnalytic = new Model('account.analytic.account');
  var QWeb = core.qweb;
  var _t = core._t;

  console.log('property_management.action_export')

  var PropertyDashboard = Widget.extend({
    template: 'PropertyDashboard',
    events: {
      'click .pos_order_today': 'pos_order_today',
      'click .pos_order': 'pos_order',
      'click .pos_total_sales': 'pos_order',
      'click .pos_session': 'pos_session',
      'click .pos_refund_orders': 'pos_refund_orders',
      'click .pos_refund_today_orders': 'pos_refund_today_orders',
      'change #pos_sales': 'onclick_pos_sales',
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

    fetch_data: function() {
      var self = this;
      var def1 = this._rpc({
        model: 'product.template',
        method: 'get_refund_details'
      }).then(function(result) {
        console.log(result)
        // self.total_sale = result['total_sale'],
        // self.total_order_count = result['total_order_count']
        // self.total_refund_count = result['total_refund_count']
        // self.total_session = result['total_session']
        // self.today_refund_total = result['today_refund_total']
        // self.today_sale = result['today_sale']
        self.selling_product = result['selling_product'];
        self.categories = result['categories']
      });


      // var def2 = self._rpc({
      //   model: "product.template",
      //   method: "get_the_top_products",
      // }).then(function (res) {
      //   console.log('get_the_top_products')
      //   console.log(res)
      //       // self.payment_details = res['payment_details'];
      //       // self.top_salesperson = res['salesperson'];
      //       // self.selling_product = res['selling_product'];
      //   });
      // return $.when(def1,def2);
      return $.when(def1);
    },

    render_dashboards: function() {
      console.log('render_dashboards')
      var self = this;
      _.each(this.dashboards_templates, function(template) {
        self.$('.o_property_dashboard').append(QWeb.render(template, {
          widget: self
        }));
      });
    },
    render_graphs: function() {
      var self = this;
      self.render_top_product_graph();
    },
    //      get_emp_image_url: function(employee){
    //        return window.location.origin + '/web/image?model=pos.order&field=image&id='+employee;
    //    },




    pos_order_today: function(e) {
      var self = this;
      var date = new Date();
      var yesterday = new Date(date.getTime());
      yesterday.setDate(date.getDate() - 1);
      console.log(yesterday)
      e.stopPropagation();
      e.preventDefault();

      session.user_has_group('hr.group_hr_user').then(function(has_group) {
        if (has_group) {
          var options = {
            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
          };
          self.do_action({
            name: _t("Today Order"),
            type: 'ir.actions.act_window',
            res_model: 'pos.order',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [
              [false, 'list'],
              [false, 'form']
            ],
            domain: [
              ['date_order', '<=', date],
              ['date_order', '>=', yesterday]
            ],
            target: 'current'
          }, options)
        }
      });

    },


    pos_refund_orders: function(e) {
      var self = this;
      var date = new Date();
      //        alert(date,"date")
      var yesterday = new Date(date.getTime());
      yesterday.setDate(date.getDate() - 1);
      console.log(yesterday)
      e.stopPropagation();
      e.preventDefault();

      session.user_has_group('hr.group_hr_user').then(function(has_group) {
        if (has_group) {
          var options = {
            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
          };
          self.do_action({
            name: _t("Refund Orders"),
            type: 'ir.actions.act_window',
            res_model: 'pos.order',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [
              [false, 'list'],
              [false, 'form']
            ],
            domain: [
              ['amount_total', '<', 0.0]
            ],

            //                    domain: [['date_order', '=', date]],
            target: 'current'
          }, options)
        }
      });

    },
    pos_refund_today_orders: function(e) {
      var self = this;
      var date = new Date();
      //        alert(date,"date")
      var yesterday = new Date(date.getTime());
      yesterday.setDate(date.getDate() - 1);
      console.log(yesterday)
      e.stopPropagation();
      e.preventDefault();

      session.user_has_group('hr.group_hr_user').then(function(has_group) {
        if (has_group) {
          var options = {
            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
          };
          self.do_action({
            name: _t("Refund Orders"),
            type: 'ir.actions.act_window',
            res_model: 'pos.order',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [
              [false, 'list'],
              [false, 'form']
            ],
            domain: [
              ['amount_total', '<', 0.0],
              ['date_order', '<=', date],
              ['date_order', '>=', yesterday]
            ],
            //                    domain: [['date_order', '=', date]],
            target: 'current'
          }, options)
        }
      });

    },

    pos_order: function(e) {
      var self = this;
      var date = new Date();
      var yesterday = new Date(date.getTime());
      yesterday.setDate(date.getDate() - 1);
      console.log(yesterday)
      e.stopPropagation();
      e.preventDefault();
      session.user_has_group('hr.group_hr_user').then(function(has_group) {
        if (has_group) {
          var options = {
            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
          };
          self.do_action({
            name: _t("Total Order"),
            type: 'ir.actions.act_window',
            res_model: 'pos.order',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [
              [false, 'list'],
              [false, 'form']
            ],
            //                    domain: [['amount_total', '<', 0.0]],
            target: 'current'
          }, options)
        }
      });

    },
    pos_session: function(e) {
      var self = this;
      e.stopPropagation();
      e.preventDefault();
      session.user_has_group('hr.group_hr_user').then(function(has_group) {
        if (has_group) {
          var options = {
            on_reverse_breadcrumb: self.on_reverse_breadcrumb,
          };
          self.do_action({
            name: _t("sessions"),
            type: 'ir.actions.act_window',
            res_model: 'pos.session',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [
              [false, 'list'],
              [false, 'form']
            ],
            //                     domain: [['state','=', In Progress]],
            target: 'current'
          }, options)
        }
      });

    },

    onclick_pos_sales: function(events) {
      var option = $(events.target).val();
      console.log('came monthly')
      var self = this
      var ctx = self.$("#canvas_1");
      rpc.query({
        model: "product.template",
        method: "get_department",
        args: [option],
      }).then(function(arrays) {
        console.log(arrays)
        var data = {
          labels: arrays[1],
          datasets: [{
              data: arrays[0],
              backgroundColor: [
                "rgba(255, 99, 132,1)",
                "rgba(54, 162, 235,1)",
                "rgba(75, 192, 192,1)",
                "rgba(153, 102, 255,1)",
                "rgba(10,20,30,1)"
              ],
              borderColor: [
                "rgba(255, 99, 132, 0.2)",
                "rgba(54, 162, 235, 0.2)",
                "rgba(75, 192, 192, 0.2)",
                "rgba(153, 102, 255, 0.2)",
                "rgba(10,20,30,0.3)"
              ],
              borderWidth: 1
            },

          ]
        };

        //options
        var options = {
          responsive: true,
          legend: {
            display: false,
            position: "bottom",
            labels: {
              fontColor: "#333",
              fontSize: 16
            }
          },
          scales: {
            yAxes: [{
              ticks: {
                min: 0
              },
              scaleLabel: {
                display: true,
                labelString: 'N° de movimientos'
              }
            }],
          }
        };

        //create Chart class object
        if (window.myCharts != undefined)
          window.myCharts.destroy();
        window.myCharts = new Chart(ctx, {
          //          var chart = new Chart(ctx, {
          type: "bar",
          data: data,
          options: options
        });

      });
    },
    render_top_product_graph: function() {
      console.log('render_top_product_graph')
      var self = this
      var ctx = self.$(".top_selling_product");
      AccountAnalytic.call("get_the_top_products", []).then(function(arrays) {
        console.log(arrays)
        var data = {
          labels: arrays[1],
          datasets: [{
              label: "Movimientos",
              data: arrays[0],
              backgroundColor: [
                "rgba(255, 99, 132,1)",
                "rgba(54, 162, 235,1)",
                "rgba(75, 192, 192,1)",
                "rgba(153, 102, 255,1)",
                "rgba(10,20,30,1)"
              ],
              borderColor: [
                "rgba(255, 99, 132, 0.2)",
                "rgba(54, 162, 235, 0.2)",
                "rgba(75, 192, 192, 0.2)",
                "rgba(153, 102, 255, 0.2)",
                "rgba(10,20,30,0.3)"
              ],
              borderWidth: 1
            },

          ]
        };

        //options
        var options = {
          responsive: true,
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
                labelString: 'N° de movimientos'
              }
            }],
          }
        };

        //create Chart class object
        var chart = new Chart(ctx, {
          type: "horizontalBar",
          data: data,
          options: options
        });

      });
    },

  });

  core.action_registry.add('property_dashboard', PropertyDashboard);

  return PropertyDashboard;



})
