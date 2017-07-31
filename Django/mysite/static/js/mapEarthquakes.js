var map;
var drawingManager;
var selectedShape;

function initMap() {

     var lleida = {lat: 41.6183423, lng: 0.6199348};
     map = new google.maps.Map(document.getElementById('map'), {
      zoom: 8,
      center: lleida,
      mapTypeId: google.maps.MapTypeId.HYBRID,
      minZoom : 3
    });


    function centerMe(position) {
        var coords = new google.maps.LatLng(
            position.coords.latitude,
            position.coords.longitude
        );
        map.setCenter(coords);
    }


     if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(centerMe);
    } else {
        alert("You don't support this");
    }

    function getSelectedShapeValues(){
        var ne = selectedShape.getBounds().getNorthEast();
        var sw = selectedShape.getBounds().getSouthWest();

        var max_lat = ne.lat();
        var min_lat = sw.lat();

        var max_lon = ne.lng();
        var min_lon = sw.lng();

        $("#max_lat").val(max_lat);
        $("#min_lat").val(min_lat);
        $("#max_lon").val(max_lon);
        $("#min_lon").val(min_lon);
    }

    function deleteSelectedShape() {
        if (selectedShape) {
            selectedShape.setMap(null);
            // To show:
            drawingManager.setOptions({
                drawingControl: true
            });
        }
    }

    function clearSelection() {
      if (selectedShape) {
        selectedShape.setEditable(false);
        selectedShape = null;
      }
    }

    function setSelection(shape) {
        clearSelection();
        selectedShape = shape;
        shape.setEditable(true);
        getSelectedShapeValues();

    }


    var polyOptions = {
        strokeWeight: 0,
        fillOpacity: 0.45,
        editable: true,
        draggable:true
    };

    var drawingManager = new google.maps.drawing.DrawingManager({
        drawingMode: google.maps.drawing.OverlayType.RECTANGLE,
        drawingControl: true,
        drawingControlOptions: {
        position: google.maps.ControlPosition.TOP_CENTER,
        drawingModes: ['rectangle']
    },
    markerOptions: {
        draggable: true
    },
    polylineOptions: {
        editable: true
    },
    rectangleOptions: polyOptions,
     map: map
    });

    google.maps.event.addListener(drawingManager, 'overlaycomplete', function(e) {
        if (e.type != google.maps.drawing.OverlayType.MARKER) {
            // Switch back to non-drawing mode after drawing a shape.
            drawingManager.setDrawingMode(null);
            drawingManager.setOptions({
                drawingControl: false
            });

            // Add an event listener that selects the newly-drawn shape when the user
            // mouses down on it.
            var newShape = e.overlay;
            newShape.type = e.type;
            google.maps.event.addListener(newShape, 'click', function() {
                setSelection(newShape);
            });
            newShape.addListener('bounds_changed', getSelectedShapeValues);
            setSelection(newShape);
        }

        google.maps.event.addListener(map, 'click', clearSelection);
        google.maps.event.addDomListener(document.getElementById('delete-button'), 'click', deleteSelectedShape);
    });
}