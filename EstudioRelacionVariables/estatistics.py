#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 14:47:58 2019
@author: natalia castejon fernandez
"""

## --   Modulos -- ##
import numpy as np
np.seterr(divide='ignore', invalid='ignore')
from scipy.stats import spearmanr
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score

## --  Funciones -- ##

def estudia_coeficientes (variables,df):
    dic_pearson={}
    dic_covar={}
    dic_spearman={}
    for i,x in enumerate (variables):
        for y in variables[i+1:]:
            df2=df.copy()
            df2=df2[np.isfinite(df2[str(x)])] 
            df2=df2[np.isfinite(df2[str(y)])]
            X=df2[str(x)].values
            Y=df2[str(y)].values
            pearson,Ppval= stats.pearsonr(X, Y)
            dic_pearson[str(x)+','+str(y)]=pearson
            dic_covar[str(x)+','+str(y)]=np.cov(X, Y)[0,1]      
            corr, Spval = spearmanr(X, Y)
            dic_spearman[str(x)+','+str(y)]=(corr)*10
      #!#!      print (str(x)+' | '+str(y),
      #!#!             "\n    Pearson: %.3f"% pearson,Ppval ,       
      #!#!             "\n    Covariate: %.3f"% np.cov(X, Y)[0,1],
      #!#!             "\n    Spearman: %.3f"% corr,Spval,)
    del df2

    
def modelo_reg_lineal(x,y):
    # Definimos el modelo lineal de prediccion
    reg=LinearRegression()
    # Entrenamos dicho modelo
    reg.fit(x,y)

    # Hacemos cross validation para conocer las metricas resultantes
    MSE=cross_val_score(reg,x,y,cv=10,scoring='neg_mean_squared_error')
    RMSE= np.sqrt(abs(MSE)).mean()
    MSE=MSE.mean()
    # Devolvemos el modelo entrenado,el valor del coef de regresion, el valor de MSE y el de RMSE
    return reg, reg.coef_, MSE, RMSE


def modelo_reg_logaritmica(x,y):
    # Definimos el modelo de prediccion
    reg=LinearRegression()
    # Entrenamos dicho modelo
    y=np.log(y)
    reg.fit(x,y)

    # Hacemos cross validation para conocer las metricas resultantes
    MSE=cross_val_score(reg,x,y,cv=10,scoring='neg_mean_squared_error')
    RMSE= np.sqrt(abs(MSE)).mean()
    MSE=MSE.mean()
    # Devolvemos el modelo entrenado,el valor del coef de regresion, el valor de MSE y el de RMSE
    return reg, reg.coef_, MSE, RMSE


def vale_valor(row):
    return float(row)


def modelo_varias_variables(variables,df,mod):
    principal=str(variables[0])
    #!#! print ('Nan en:',principal,pd.isna(df[principal]).sum() )
    for var1 in variables[1:]:
        df2=df[variables].copy()
        df2=df2[np.isfinite(df2[principal])]
        df2=df2[np.isfinite(df2[str(var1)])]
        modelo, reg_coef, MSE, RMSE=mod(df2[[principal]],df2[str(var1)])    
        
        #modelo, reg_coef, MSE, RMSE=modelo_reg_lineal(df2[[principal]],df2[str(var1)])    
        df[principal]=[modelo.predict([[df.loc[i,str(var1)]]])[0] if (str(row) in ['nan','']) & (np.isfinite(df.loc[i,str(var1)])) else vale_valor(row) for  i,row in enumerate(df[principal])] 
    #!#! print('Tras',var1,':', pd.isna(df[principal]).sum())   
    #!#! print ('MSE:',MSE,'\nRMSE:',RMSE)
    return df[principal]


def relleno_y_reduccion(df):
    ############################## 
    # Estudio de la relacion entre variables: Eliminamos valores nan y calculamos correlacion
    ##############################
    
    ### Variables de frecuencia poblacional
    variables=['maf', 'gnomAD_genome_ALL', '1000g2015aug_all', '1000G_ALL', 'ExAC_ALL',
               'AF', 'PopFreqMax', '5000Exomes']
    estudia_coeficientes (variables,df)
    
    
    ### Predictores, algunos hay que normalizarlos : 
    # PROVEAN [-14, 14], CADD [0, 99], phylop [-20 , 30], grantham [5, 215]
    variables=['SIFT_score', 'sift','ljb23_sift',
               'Polyphen2_HDIV_score', 'Polyphen2_HVAR_score', 'polyphen', 
               'phyloP20way_mammalian','phylop',
               'MutationTaster_score', 
               'PROVEAN_score', 
               'CADD_phred', 
               'FATHMM',
               'grantham','FATHMM_score','SiPhy_29way_logOdds']
    
    df['PROVEAN_score']=(df['PROVEAN_score']+14) / 28
    df['CADD_phred']=(df['CADD_phred']) / 99
    df['phylop']=(df['phylop'] +20)/50
    df['grantham']=(df['grantham']-5)/ 215
    
    estudia_coeficientes (variables,df)
    
    
    ### Variables ordinales
    variables=['Func.refGene', 'ExonicFunc.refGene', 'function', 'clinvar']
    estudia_coeficientes (variables,df)


    ##############################
    # Generacion de nuevas variables y reduccion de dimensionalidad
    ##############################
    
    ### Generamos FRECUENCIA_t: A partir de 5000Exomes rellenamos nan de maf:
    variables=['maf','5000Exomes']
    #!#! print('Nan en maf:',pd.isna(df['1000G_ALL']).sum())
    df['FRECUENCIA_t']=modelo_varias_variables(variables,df,modelo_reg_lineal)     
    #!#! print('Nan en FRECUENCIA_t:',pd.isna(df['FRECUENCIA_t']).sum())
    
    
    ### Generamos POBLACION_t: A partir de 1000g2015aug_all + gnomAD_genome_ALL + AF + ExAC_ALL + PopFreqMax rellenando sobre nan de 1000G_ALL
    variables=['1000G_ALL','1000g2015aug_all','gnomAD_genome_ALL','AF','ExAC_ALL','PopFreqMax']
    #!#! print('Nan en 1000G_ALL:',pd.isna(df['1000G_ALL']).sum())
    df['POBLACION_t']=modelo_varias_variables(variables,df,modelo_reg_lineal)     
    #!#! print('Nan en POBLACION_t:',pd.isna(df['POBLACION_t']).sum())
    
    
    ### Generamos SIFT_t: A partir de [SIFT_score <- sift <- 	 ljb23_sift] (modelo r.lineal) <- PROVEAN (modelo r. logarítmica)
    variables=['SIFT_score','sift','ljb23_sift']
    #!#! print('Nan en SIFT_score:',pd.isna(df['SIFT_score']).sum())
    df['SIFT_previo']=modelo_varias_variables(variables,df,modelo_reg_lineal) 
    variables=['SIFT_previo','PROVEAN_score']
    df['SIFT_t']=modelo_varias_variables(variables,df,modelo_reg_logaritmica) 
    #!#! print('Nan en SIFT_t:',pd.isna(df['SIFT_t']).sum())

    
    ### Generamos POLYPHEN_t: A partir de polyphen <- Polyphen2_HDIV_score <- Polyphen2_HVAR_score <- CADD_phred
    variables=['Polyphen2_HDIV_score','Polyphen2_HVAR_score','CADD_phred']
    #!#! print('Nan en Polyphen2_HDIV_score:',pd.isna(df['Polyphen2_HDIV_score']).sum())
    df['POLYPHEN_t']=modelo_varias_variables(variables,df,modelo_reg_lineal)
    #!#! print('Nan en POLYPHEN_t:',pd.isna(df['POLYPHEN_t']).sum())
    
    
    ### Generamos PHYLOP_t: A partir de phylop <- phyloP20way_mammalian	<- [ FATHMM <- FATHMM_score] <- SiPhy_29way_logOdds
    variables=['phyloP20way_mammalian','FATHMM','FATHMM_score','SiPhy_29way_logOdds']
    #!#! print('Nan en phyloP20way_mammalian:',pd.isna(df['phyloP20way_mammalian']).sum())
    df['PHYLOP_t']=modelo_varias_variables(variables,df,modelo_reg_lineal)
    #!#! print('Nan en PHYLOP_t:',pd.isna(df['PHYLOP_t']).sum())
    
    
    ### Generamos FUNCTIN_t: A partir de 'ExonicFunc.refGene' y  'function'
    variables=['ExonicFunc.refGene', 'function']
    #!#! print('Nan en ExonicFunc.refGene:',pd.isna(df['ExonicFunc.refGene']).sum())
    df['FUNCTION_t']=modelo_varias_variables(variables,df,modelo_reg_lineal)
    #!#! print('Nan en FUNCTION_t:',pd.isna(df['FUNCTION_t']).sum())

    df['Func.refGene']=df['Func.refGene'].astype('category')
    df['FUNCTION_t']=df['FUNCTION_t'].astype('category')      
    df['clinvar']=df['clinvar'].astype('category')


    ### Eliminamos columnas sobrantes
    df=df.drop(columns=['maf','5000Exomes',
             '1000G_ALL','1000g2015aug_all','gnomAD_genome_ALL','AF','ExAC_ALL','PopFreqMax',
             'SIFT_score','sift','ljb23_sift','SIFT_previo','PROVEAN_score',
             'Polyphen2_HDIV_score','Polyphen2_HVAR_score','CADD_phred',
             'phyloP20way_mammalian','FATHMM','FATHMM_score','SiPhy_29way_logOdds',
             'ExonicFunc.refGene', 'function'])


    return df



