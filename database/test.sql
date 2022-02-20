with mavue as (
select distinct tab_check.*, 
figures.bullish_engulfing, 
figures.hanging_man,
figures.bearish_engulfing,
figures.bullish_harami,
figures.hammer
--prediction.o_sell,
--prediction.o_buy,
--prediction.o_neutral,
--prediction.o_result_fin
from tab_check
inner join figures on tab_check.date = substring(cast(figures.time_debut as text), 0 , 17)
--inner join prediction on tab_check.monnaie = prediction.monnaie and tab_check.date = substring(cast(prediction.res_date as text), 0 , 17)
--where prediction.prevision = '5 MINUTES' and
where figures.bullish_engulfing != 'NaN' and figures.hanging_man != 'NaN' and figures.bearish_engulfing != 'NaN' and figures.hammer != 'NaN' 
--and prediction.o_result_fin = 'NEUTRAL'
order by date desc
),
clean as (
select 
	case when check_win = '-1' and action = 'put' and bearish_engulfing = 'True' then 1 else 0 end as cptr_eng_bear,
	case when bearish_engulfing = 'True' then 1 else 0 end as eng_bear,
	case when check_win = '-1' and action = 'call' and bullish_engulfing = 'True' then 1 else 0 end as cptr_eng_bull,
	case when bullish_engulfing = 'True' then 1 else 0 end as eng_bull,
	case when check_win = '-1' and action = 'call' and hanging_man = 'True' then 1 else 0 end as cptr_hanging_man,
	case when hanging_man = 'True' then 1 else 0 end as hanging_man,
	case when check_win = '-1' and action = 'put' and hammer = 'True' then 1 else 0 end as cptr_hammer,
	case when hammer = 'True' then 1 else 0 end as hammer,
	case when check_win = '-1' and action = 'call' and bullish_harami = 'True' then 1 else 0 end as cptr_bullish_harami,
	case when bullish_harami = 'True' then 1 else 0 end as bullish_harami
	from mavue
)


select sum(cptr_eng_bear) as cptr_eng_bear, 
sum(eng_bear) as eng_bear,
sum(cptr_eng_bull) as cptr_eng_bull, 
sum(eng_bull) as eng_bull,
sum(cptr_hanging_man) as cptr_hanging_man, 
sum(hanging_man) as hanging_man,
sum(cptr_hammer) as cptr_hammer, 
sum(hammer) as hammer,
sum(cptr_bullish_harami) as cptr_bullish_harami, 
sum(bullish_harami) as bullish_harami
from clean 
/*
select check_win, hammer from clean where action = ""
*/
--select sum(cast(Check_win as integer)) from test group by substring(cast(date as text), 0 , 11)
--where bullish_engulfing != 'False' and hanging_man != 'False' and bearish_engulfing != 'False' and hammer != 'False'


"GBPUSD"
"GBPCAD"
"AUDCAD"
"EURJPY"
"GBPJPY"
"EURGBP"
"AUDUSD"
"EURUSD"