var mapomat = angular.module('mapomat', []);

mapomat.controller('SelectController', function SelectController($window) {
        this.cityCats = $window.cityCategories
        this.superNames = $window.superCatNames
        this.subNames = $window.subCatNames
    });

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
