for FILE in data/Local_Hesse_2016/*; do
    bn=`basename $FILE`
    python3 audit.py -d $FILE -r 0.20 -g 0.1 > output/output_$bn 
done

python3 analyse.py output/ 
