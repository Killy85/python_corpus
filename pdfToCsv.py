#!/usr/bin/env python
# -*- coding: utf-8 -*

import PyPDF2
import re
import sys
import sqlite3
import MySQLdb

caps = "([A-Z])"
prefixes = "(Mr|St|Mrs|Ms|Dr|Mme|M)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|fr|gouv)"
paramMysql = {
    'host'   : 'localhost',
    'user'   : 'root',
    'passwd' : 'root',
    'db'     : 'french_training'
}


class Converter:
	def to_str(self,tab):
	    ret =''
	    for fragment in [x.encode('UTF8') for x in tab]:
	        ret += fragment+" "
	    return ret

	def split_into_sentences(self,text):
	    text = " " + text + "  "
	    text = text.replace("\n"," ")
	    text = re.sub(prefixes,"\\1<prd>",text)
	    text = re.sub(websites,"<prd>\\1",text)
	    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
	    text = re.sub("\s" + caps + "[.] "," \\1<prd> ",text)
	    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
	    text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
	    text = re.sub(caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>",text)
	    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
	    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
	    text = re.sub(" " + caps + "[.]"," \\1<prd>",text)
	    if "!" in text: text = text.replace("!\"","\"!")
	    if "?" in text: text = text.replace("?\"","\"?")
	    text = text.replace(".","<stop>")
	    text = text.replace(",","<stop>")
	    text = text.replace("?","<stop>")
	    text = text.replace("!","<stop>")
	    text = text.replace(";","<stop>")
	    text = text.replace(":","<stop>")
	    text = text.replace("'"," ")
	    text = text.replace("<prd>",".")
	    text = text.replace(u"\u2122", ' ')
	    sentences = text.split("<stop>")
	    sentences = sentences[:-1]
	    sentences = [s.strip() for s in sentences]
	    sentences = self.remove_line_number(sentences)
	    return sentences

	def remove_line_number(self,sentences):
	    returned_sentences= []
	    for sentence in sentences:
	        if(sentence!=""):
	            phrase = sentence.split(" ")
	            try:
	                int(phrase[0])
	                returned_sentences.append(self.to_str(phrase[1:]))
	            except ValueError:
	                returned_sentences.append(sentence)
	    return returned_sentences


	def compute(self,path, indexBeg=1):
	  	text =""
	  	sql = """\
		INSERT INTO samples(path_txt) VALUES 
		"""
	  	index=indexBeg
	  	if(path[-4:] == ".pdf"):
			pdfFileObj = open(path, 'rb')
			pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
			nbPage = pdfReader.getNumPages()
			for i in range(1,nbPage):
			    pageObj = pdfReader.getPage(i)
			    text += (pageObj.extractText()[:-5]+ " ")

		elif(path[-4:] == ".txt"):
			with open(path,"r") as f:
				for line in f.readlines():
					if(line!=""):
						text += line.decode('UTF-8')
		else:
			print(path[-4:])
		sentences = self.split_into_sentences(text)
		for sentence in sentences:
		    if(sentence != ""):
		    	with open("sentences/" +str(index) +'.txt', 'w') as f:
		    		try:
		        		f.write(sentence.encode('UTF-8'))

		        	except:
		        		f.write(sentence)
		        sql += '("~/Documents/DataTraining/sentences/' +str(index) +'.txt"),'
		        index +=1
		sql = sql[:-1] + ";"
		conn = MySQLdb.connect(**paramMysql)
		cur = conn.cursor(MySQLdb.cursors.DictCursor)
		if(cur.execute(sql)):
			print("yes")
		conn.close()
		return index

if __name__ == '__main__':
	cv = Converter()
	if(len(sys.argv) == 2): 
		print("You have saved %s sentences"% cv.compute(sys.argv[1]))
	elif (len(sys.argv) < 2):
		print("You have to define a path to a PDF or TXT file")
	else:
		nbphrases=1
		for i in range (1,len(sys.argv)):
			nbphrases = cv.compute(sys.argv[i],nbphrases)
			print("%s sentences written, file %s"% (nbphrases,i-1))