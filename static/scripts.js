document.addEventListener("DOMContentLoaded", function () {
    // Selecione o botão de confirmação e a caixa de datas
    const cabinId = getCabinIdFromURL();
    const confirmButton = document.getElementById("confirmButton");
    const datePicker = document.getElementById("datePicker");

    // Selecione a div onde você deseja exibir a data selecionada
    const agendamentosDiv = document.getElementById("agendamentos");

    // Selecione a div onde você deseja exibir o conteúdo do arquivo JSON
    const cabinsContentDiv = document.getElementById("cabinsContent");

    // Função para formatar a data no formato "dd-mm-aaaa"
    function formatDate(selectedDate) {
        const options = { year: 'numeric', month: 'numeric', day: 'numeric' };
        return selectedDate.toLocaleDateString(undefined, options);
        }


    // Função para formatar a data no formato "dd-mm-aaaa"
    function formatDate(selectedDate) {
        const dateObj = new Date(selectedDate);
        const day = (dateObj.getDate() + 1).toString().padStart(2, "0");
        const month = (dateObj.getMonth() + 1).toString().padStart(2, "0");
        const year = dateObj.getFullYear();
        return `${day}-${month}-${year}`;
    }

    function getCabinIdFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const cabinId = urlParams.get("cabin_id");
        return cabinId;
    }     

        // Função para carregar e exibir o conteúdo do arquivo JSON
    function loadCabinsData(cabinId, dia) {
        
        // Você pode substituir o caminho 'cabins.json' pelo caminho real do seu arquivo JSON
        fetch('../data/cabins.json')
            .then(response => response.json())
            .then(data => {
                // Filtrar as cabines com o ID igual a cabinId
                const filteredCabins = data.filter(cabin => cabin.id === cabinId);
                // Verificar se alguma cabine foi encontrada
                if (filteredCabins.length > 0) {
                    // Filtrar os agendamentos do dia 
                    const agendamentosDia = filteredCabins[0].agendamentos.filter(agendamento => agendamento.dia.includes(dia));

                    console.log(filteredCabins)
                    console.log(agendamentosDia)
                    if(dia != "NaN-NaN-NaN"){
                        // Verificar se existem agendamentos para o dia 
                        if (agendamentosDia.length >= 0) {
                            // Exiba apenas os agendamentos do dia na div cabinsContent                
                            createTable(dia, agendamentosDia, cabinId);
                        }
                    }

                } else {
                    cabinsContentDiv.textContent = `Nenhuma cabine encontrada com o ID ${cabinId}.`;
                }
            })
            .catch(error => {
                console.error('Erro ao carregar o arquivo JSON:', error);
            });
    }

    function createTable(formattedDate, horarios, cabinId){
        // Array to store the "hora" values
        const horaValues = [];

        // Loop through the JSON data and extract "hora" values
        horarios.forEach(item => {
        horaValues.push(item.hora);
        });

        const table = document.createElement("table");

        // Create a div element for the popup
        const popupDiv = document.createElement("div");
        popupDiv.classList.add("popup");
        popupDiv.textContent = "Horário indisponível";
        popupDiv.style.display = "none"; // Initially hide the popup
        document.body.appendChild(popupDiv);

        // Crie o cabeçalho da tabela (opcional)
        for (let hour = 9; hour < 18; hour++) {
            const row = document.createElement("tr");
            const cell = document.createElement("td");

            // Formate a hora para incluir zeros à esquerda, se necessário
            const formattedHour = hour.toString().padStart(2, "0");
            // Adicione a hora à célula
            cell.textContent = `${formattedHour}:00`;

            // Check if the hour should be clickable
            const isClickableHour = !horaValues.includes(`${formattedHour}:00`); // Replace with your condition
            if (isClickableHour) {
                // Adicione um evento de clique à célula
                cell.addEventListener("click", function () {
                    // Pegue o valor da hora clicada
                    const clickedHour = `${formattedDate} ${formattedHour}:00`;

                    // Redirecione o usuário para a rota Flask "agendar" com o dia e a hora como parte do URL
                    window.location.href = `/${cabinId}/${clickedHour}`;
                });
            } else {
                // Format the text as gray
                cell.style.color = "gray";
                // Add a click event to display the popup
                cell.addEventListener("click", function () {
                    // Show the popup
                    popupDiv.style.display = "block";
                });
            }

            // Adicione a célula à linha
            row.appendChild(cell);

            // Adicione a linha à tabela
            table.appendChild(row);
        }
        
        // Anexe a tabela à div onde você deseja exibi-la
        agendamentosDiv.appendChild(table);
    }

    // Adicione um evento de clique ao botão de confirmação
    confirmButton.addEventListener("click", function () {
        // Obtenha a data selecionada
        const selectedDate = new Date(datePicker.value);
        const formattedDate = formatDate(selectedDate);

        const url = window.location.href;
        const parts = url.split("/");
        const cabinId = parts[parts.length - 1];

        // Verifique se a data é válida (você pode adicionar validações adicionais aqui)
        if (selectedDate) {
            // Limpe qualquer conteúdo anterior na div de agendamentos
            agendamentosDiv.innerHTML = "";
        
            loadCabinsData(parseInt(cabinId), formattedDate);
        } else {
            // Se nenhuma data for selecionada, exiba uma mensagem de erro
            agendamentosDiv.innerHTML = "Selecione uma data válida.";
        }
    });
});
