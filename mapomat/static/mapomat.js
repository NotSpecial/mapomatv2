var mapomat = angular.module('mapomat', ['ui', 'minicolors']);

mapomat.controller('SelectController', 
  ['$window', '$scope', '$http', function($window, $scope, $http) {
    $scope.cityCats = $window.cityCategories;
    $scope.superNames = $window.superCatNames;
    $scope.subNames = $window.subCatNames;
    $scope.sendFormTo = $window.sendFormTo;
    $scope.selection = {};
    $scope.colors = [];
    $scope.advancedOptions = false;

    // configuration for color picker
    $scope.pickerConfig = {
        control: 'wheel',
        position: 'top right',
        theme: 'mapomat',
    }

    var colorPicker = function(selection, superNames, subNames) {
      // search for selected 
      var selected = [];
      for (var key in selection) {
        if (selection[key]) {
          // only in this case selection is true
          selected.push(key);
        }
      }
      
      // update colors
      var colors = [];
      var numcolors = selected.length;
      for (var i = 0; i < numcolors; i++) {
        var hue = i * 1.0 / numcolors;
        //get the name
        var name = "";
        var key = "";
        if (selected[i] in superNames) {
          name = superNames[selected[i]];
          key = selected[i];
        }
        else {
          var subcat = JSON.parse(selected[i]);
          if (subcat[0] in subNames && subcat[1] in subNames[subcat[0]]) {
            name = subNames[subcat[0]][subcat[1]];
            // get this back to python tuple format
            key = '(' + subcat[0] + ', ' + subcat[1] + ')';
          }
        }
        var color = {
          "key": key,
          "name": name,
          "color": hslToHex(hue, 1, 0.5)
        };
        colors.push(color);
      }
      return colors;
    };
  
    $scope.updateColors = function() {
      $scope.colors = colorPicker($scope.selection, $scope.superNames,
        $scope.subNames);
    };

    $scope.sendForm = function() {
      var data = {
        city: $scope.selectedCity,
        colors: $scope.colors,
        selected: $scope.selection
      };

      var config = {
        headers : {
          'Content-Type': 'application/json'
        }
      };

      res = $http.post($scope.sendFormTo, data, config)
      res.success(function(data, status, headers, config) {
        // load result window
        $window.location.assign("result/" + data)
      });
      res.error(function(response) {
        alert(response);
      });
    };
}]);


mapomat.controller('LegendController', function LegendController() {
        this.show = true
    });
/*
mapomat.controller('FooterController', function FooterController($window) {

    this.footerMargin = {"margin-top": 100 + "px"}
    console.log(this.footerMargin)

    });
<script>
    $(document).ready(function() {

        var docHeight = $(window).height();
        var footerHeight = $('#footer').height();
        var footerTop = $('#footer').position().top + footerHeight;

        if (footerTop < docHeight) {
         $('#footer').css('margin-top', 10+ (docHeight - footerTop) + 'px');
        }
    });
    </script>
*/


var componentToHex = function(c) {
    var hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
};

/**
 * Converts an HSL color value to RGB. Conversion formula
 * adapted from http://en.wikipedia.org/wiki/HSL_color_space.
 * Assumes h, s, and l are contained in the set [0, 1] and
 * returns r, g, and b in the set [0, 255].
 *
 * @param   Number  h       The hue
 * @param   Number  s       The saturation
 * @param   Number  l       The lightness
 * @return  Array           The RGB representation
 */
var hslToHex = function(h, s, l){
    var r, g, b;

    if(s === 0){
        r = g = b = l; // achromatic
    }else{
        var hue2rgb = function hue2rgb(p, q, t){
            if(t < 0) t += 1;
            if(t > 1) t -= 1;
            if(t < 1/6) return p + (q - p) * 6 * t;
            if(t < 1/2) return q;
            if(t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        };

        var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        var p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }

    r_hex = componentToHex(Math.round(r * 255));
    g_hex = componentToHex(Math.round(g * 255));
    b_hex = componentToHex(Math.round(b * 255));
    return '#' + r_hex + g_hex + b_hex;
};
