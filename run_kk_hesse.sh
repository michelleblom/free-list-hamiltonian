for FILE in data/Local_Hesse_2016/*; do
    bn=`basename $FILE`
    python3 audit.py -d $FILE -r 0.10 -g 0.1 -e 0 > output_10pc/output_$bn 
    python3 audit.py -d $FILE -r 0.20 -g 0.1 -e 0 > output_20pc/output_$bn 
    python3 audit.py -d $FILE -r 0.05 -g 0.1 -e 0 > output_05pc/output_$bn 
done

echo "5 PC"
python3 analyse.py output_05pc
echo "10 PC"
python3 analyse.py output_10pc
echo "20 PC"
python3 analyse.py output_20pc
