
        function taggleById(id){
            var div = document.getElementById(id);
            if(div.style.display === "none"){
                div.style.display = "block";
            } else {
                div.style.display = "none";
            }
        }

        function taggleAllSections(elements){
            alert(document.getElementById("accordion-header-1").innerText);
            if(document.getElementById("all").innerText === "Hide all sections"){
                for(let i=1; i<=elements; i++){
                    document.getElementById(i).style.display = "none";
                }
                document.getElementById("all").innerText = "Show all sections"
            } else {
                for(let i=1; i<=elements; i++){
                    document.getElementById(i).style.display = "block";
                }
                document.getElementById("all").innerText = "Hide all sections";
            }
        }