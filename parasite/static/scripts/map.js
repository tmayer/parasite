
    // size of svg 
    var width = 800, height = 400;
    var radSmall = 3;
    var radFocus = 5;
    var scaleFactor = 1;
    // projection settings 
    var projection = d3.geo.equirectangular() 
        .center([38, -25 ]) 
        .scale(120)
        ;
    // boolean free variable for freezing info box
    var freeze = false;
    // make basic plot 
    var svg = d3.select("#map").append("svg") 
        .attr("width", width)
        .attr("height", height)
        ;
                
        
    var g = svg.append("g");
    var mapPoly = g.append('g').attr('class','mapPoly') // for the map
    var nodeCircles = g.append('g').attr('class','nodeCircles') // for the 
                                                                // locations
    // define scales and projections 
    var path = d3.geo.path()
        .projection(projection);
        


        
    // load and display the World
    d3.json("/static/data/world-110m.json", function(error, topology) { 
        var countrydata = topojson.object(topology,
            topology.objects.countries).geometries;          
        mapPoly.selectAll("path")
            .data(topojson.object(topology, topology.objects.countries) 
            .geometries) 
            .enter() 
            .append("path")
            .attr("d", path) 
            .style("fill","#c0c0c0")
            .style('stroke','white')
            .style('stroke-width',function(d){
                return 1/scaleFactor;
            })
            ; 
    });
    
    // load data 
    d3.json("/static/data/languages.json", function(data) {
        
        //############### PLOT SYMBOLS FOR LOCATIONS ###############
        nodeCircles.selectAll("circle") 
            .data(data.languages) 
            .enter() 
            .append("circle") 
            .attr('class',function(d,i){
              return 'node node_' + d.code;  
            })
            .attr("cx", function(d) {
                return projection([d.longitude, d.latitude])[0];
            })
            .attr('cy',function(d){
                return projection([d.longitude, d.latitude])[1]; 
            }) 
            .attr("r",function(d){
                return radSmall/scaleFactor;
            })
            .style("fill", "DarkGreen") 
            .style("stroke","white") 
            .style("stroke-width", function(d){
                return 1/scaleFactor;
            }) 
            .style("cursor","pointer")
            .on('mouseover',function(d,i){
                if(freeze == false){
                    d3.selectAll('.node').style("fill","DarkGreen")
                        .attr("r",radSmall/scaleFactor)
                        .style('stroke-width',function(d){
                            return 1/scaleFactor;
                        }); 
                    d3.select(this).style("fill","FireBrick")
                        .attr("r",radFocus/scaleFactor) 
                        .style('stroke-width',function(d){
                            return 2/scaleFactor;
                        })
                    ;
                    var sel = d3.select(this);
                      sel.moveToFront();
                    //console.log(d);
                    d3.select('#info')
                    .html(function(){
                       return infoBox(d.name,d.code,d.texts);
                    })
                    .classed('hidden',false)
                    ;
                    d3.select("#close").classed('hidden',false);
                }
            })
            .on('mouseout',function(){
              if(freeze == false){
                  d3.selectAll('.node').style("fill","DarkGreen")
                  .attr("r",radSmall/scaleFactor)
                  .style('stroke-width',function(d){
                      return 1/scaleFactor;
                  }); 
                  

                  d3.select("#info").classed('hidden',true);

                  d3.select("#close").classed('hidden',true);
              }  
            })
            .on('click',function(d,i){
              freeze = true;  
            })
            .append('title')
            .text('Click to freeze information window')
        ;
        

        d3.selection.prototype.moveToFront = function() {
          return this.each(function(){
            this.parentNode.appendChild(this);
          });
        };
         
        d3.select('#close')
            .on('click',function(){
                //console.log('click');
                d3.selectAll('.node').style("fill","DarkGreen")
                .attr("r",function(d){
                    return radSmall/scaleFactor;
                }) 
                .style('stroke-width',function(d){
                    return 1/scaleFactor;
                })
                ;
                d3.select("#info").classed('hidden',true);

                d3.select(this).classed('hidden',true);

                d3.selectAll('.lang').classed('active',false);
                $("#searchfield").val("");
                freeze = false;
            })
        ;
         
        // make info box draggable
	    $(function() {
	      $("#draggable").draggable();
	    });
            
        // autocomplete for search box
        var availableTags = [];
        var nameByCode = {};
        data.languages.forEach(function(a){
            availableTags.push(a.name + " [" + a.code + "]");
            nameByCode[a.name + " [" + a.code + "]"] = [a.code,a.texts];
        });

        $( "#searchfield" ).autocomplete({
          source: availableTags
        });
        
        
        // listener to autocomplete
        $( "#searchfield" ).autocomplete({
            select: function(event, ui) { 
           name = $(ui)[0].item.value
           codetag = nameByCode[name];
           name = name.substring(0,name.length - 6);
           
           if(codetag){
               code = codetag[0];
           
           
           d3.selectAll('.node').style("fill","DarkGreen")
           .attr("r",function(d){
               return radSmall/scaleFactor;
           }) 
           .style('stroke-width',function(d){
               return 1/scaleFactor;
           })
           ;
           
           
           d3.selectAll('.node_' + code).style("fill","FireBrick")
               .attr("r",function(d){
                   return radFocus/scaleFactor;
               }) 
               .style('stroke-width',function(d){
                   return 2/scaleFactor;
               })
           ;
           
           freeze = true
       
           var sel = d3.select('.node_' + code);
             sel.moveToFront();
             
             
             // info box
             texts = codetag[1];
             d3.select('#info')
             .html(function(){
                return infoBox(name,code,texts);
             })
             .classed('hidden',false)
             ;
             d3.select("#close").classed('hidden',false);
           }
       }
           
        });
        
        // generate info box contents
        function infoBox(name,code,texts){
            var output_string =  "<table class=\"infobox\">" + 
            "<tr><td colspan=\"2\" class='tablehead'><b>" + name + 
            "</b> [" + code + "]</td></tr>";
            var count = 1;
            txtstring = "Available translation:"
            if(texts.length > 1){
                txtstring = "Available translations:"
            }
            output_string = output_string + "<tr><td colspan='2'><i>" + 
                txtstring + "</i></td></tr>"
            texts.forEach(function(a){
               var parts = a.split('-'); 
               var textname = parts[3];
               var urlname = parts[0] + "-x-bible-" + parts[3];
               output_string = output_string + "<tr><td class='firsttd'>" + 
               count + ") </td><td>" + 
               "<a href='" + 
               urlname + "' title='" + urlname + "'>" + 
               textname 
               + "</a>" + 
               "</td></tr>";
               count = count + 1;
            });
            
            var output_string = output_string + "</table>";
            
            return output_string;
        };
        
        
          
            
    });
    
    function clicked(d) {
      var centroid = path.centroid(d),
          translate = projection.translate();

      projection.translate([
        translate[0] - centroid[0] + width / 2,
        translate[1] - centroid[1] + height / 2
      ]);

      zoom.translate(projection.translate());

      g.selectAll("path").transition()
          .duration(1000)
          .attr("d", path);
    }
    
    // zoom and pan
    
    var zoom = d3.behavior.zoom()
        .scaleExtent([1, 8])
        .on("zoom",function() {
            g.attr("transform","translate("+ 
                d3.event.translate.join(",")+")scale("+d3.event.scale+")");
            g.selectAll("circle")
                .attr("d", path.projection(projection))
                .attr("r",function(d){
                    scaleFactor = d3.event.scale;
                    return radSmall/d3.event.scale;
                })
                .style('stroke-width',function(d){
                    return 1/d3.event.scale;
                })
            ;
            g.selectAll("path")  
                .attr("d", path.projection(projection))
                .style('stroke-width',function(d){
                    return 1/d3.event.scale;
                }); 
                

      });
      
      d3.select('#resetmap').on('click',function(a){
         g.attr('transform','translate(0,0)');
         scaleFactor = 1;
         g.selectAll("circle")
                         .attr("d", path.projection(projection))
                         .attr("r",function(d){
                             return radSmall/scaleFactor;
                         })
                         .style('stroke-width',function(d){
                             return 1/scaleFactor;
                         })
                     ;
         g.selectAll("path")  
             .attr("d", path.projection(projection))
             .style('stroke-width',function(d){
                 return 1/scaleFactor;
             }); 
             
             zoom.scale(1);
             zoom.translate([0,0]);
         
          
      });

    svg.call(zoom)

