import copy
from database.distributore_DAO import DistributoreDAO
from model.distributore_DTO import Distributore

'''
    MODELLO:
    - Rappresenta la struttura dati
    - Si occupa di gestire lo stato dell'applicazione
    - Interagisce con il database
'''

class Model:
    def __init__(self):
        self._distributori = None
        self.load_distributori()

        self.__sequenza_ottima = []
        self.__costo_ottimo = -1

    def load_distributori(self):
        """ Carica tutti i distributori e li setta nella variabile self._distributori """
        self._distributori = DistributoreDAO.get_distributori()

    def get_prezzo_medio(self, mese:int):
        """
        Calcola, per ogni distributore, il prezzo medio al litro per il mese selezionato.
        :param mese: Mese selezionato (un intero da 1 a 12)
        :return: lista di tuple --> (nome del distributore, media), es. (Distributore A, 1.789)
        """
        risultati = []
        for distributore in self._distributori:
            prezzi = distributore.get_prezzi()

            # Estraggo i prezzo_litro solo per i record in cui p.data.month == mese
            prezzi_mese = [p.prezzo_litro for p in prezzi if p.data.month == mese]

            # Calcolo la media (se prezzi_mese non è vuota) e aggiungo (distributore.nome, media) a risultati
            if len(prezzi_mese) > 0:
                media = round(sum(prezzi_mese) / len(prezzi_mese), 3)
                risultati.append((distributore.nome, media))

        return risultati

    def get_sequenza_ottima(self, mese:int):
        """
        Calcola la sequenza ottimale di rifornimenti nei primi 7 giorni
        :return: sequenza di nomi distributore ottimale
        :return: costo ottimale (cioè quello minimizzato dalla sequenza scelta)
        """
        self.__sequenza_ottima = []
        self.__costo_ottimo = -1
        prezzi_settimana = self.__get_prezzi_prima_settimana_mese(mese)

        self.__ricorsione([], 1, None, 0, prezzi_settimana)

        # Traduci gli ID in nomi
        id_to_nome = {distributore.id: distributore.nome for distributore in self._distributori}
        sequenza_nomi = [f"Giorno {giorno}: {id_to_nome[i]}" for giorno, i in enumerate(self.__sequenza_ottima, start=1)]
        return sequenza_nomi, round(self.__costo_ottimo, 2)

    def __ricorsione(self, sequenza_parziale, giorno, ultimo_distributore, costo_corrente, prezzi_settimana):
        """ Implementa la ricorsione """
        # Condizione terminale: pianificati tutti e 7 i giorni
        if giorno > 7:
            if self.__costo_ottimo == -1 or costo_corrente < self.__costo_ottimo:
                self.__costo_ottimo = costo_corrente
                self.__sequenza_ottima = copy.deepcopy(sequenza_parziale)
            return

        # Pruning (opzionale ma utile)
        if self.__costo_ottimo != -1 and costo_corrente >= self.__costo_ottimo:
            return

        # Ciclo sui distributori disponibili
        for id_dist in prezzi_settimana.keys():
            # Calcolo del costo per il giorno corrente (100 litri + eventuale spostamento di 5€)
            costo_carburante = prezzi_settimana[id_dist][giorno - 1] * 100
            costo_spostamento = 5 if (ultimo_distributore is not None and id_dist != ultimo_distributore) else 0
            nuovo_costo = costo_corrente + costo_carburante + costo_spostamento

            # Aggiungo la scelta e scendo al giorno successivo
            sequenza_parziale.append(id_dist)
            self.__ricorsione(sequenza_parziale, giorno + 1, id_dist, nuovo_costo, prezzi_settimana)

            # Backtracking
            sequenza_parziale.pop()

    def __get_prezzi_prima_settimana_mese(self, mese: int):
        """
        Restituisce i prezzi dei primi 7 giorni del mese selezionato per ciascun distributore.
        :return: un dizionario: {id_distributore: [prezzo_giorno1, ..., prezzo_giorno7]}
        """
        prezzi_settimana = {}
        for distributore in self._distributori:
            prezzi = distributore.get_prezzi()
            # Filtro i primi 7 giorni del mese selezionato e li ordino per giorno
            prezzi_filtrati = [p for p in prezzi if p.data.month == mese and p.data.day <= 7]
            prezzi_ordinati = sorted(prezzi_filtrati, key=lambda p: p.data.day)

            # Salvo solo i valori float dei prezzi al litro
            prezzi_settimana[distributore.id] = [p.prezzo_litro for p in prezzi_ordinati]

        return prezzi_settimana