dataset1 <- loan.data

for (i in 1:nrow(dataset1)){
  
  if (identical(substring(dataset1$Monthly.Debt[i], 1, 1),"$"))
  {
    print(i)
    print(dataset1$Monthly.Debt[i])
    dataset1$Monthly.Debt[i] <- substring(dataset1$Monthly.Debt[i], 2)
    print(dataset1$Monthly.Debt[i])
    
  }
}
