"""classification.py: Implements a relevance vector machine."""

import numpy as np
import matplotlib.pyplot as plt
import math
import pdb # for debugging

def main():
    ## By Foteini Beligianni and David Huebner
    raetschDataset = False # when true one of hte Raetsch datasets (Banana, titanic, etc) is to be classified, false otherwise

    # Train RVM. We have to choose the hyper-parameter r depending on the data_set
    # for Ripley, take r = 0.5
    # for Pima, take r = 150
    # for Breast Cancer, take r = 4
    # for Titanic, take r = 4
    # for German, take r = 10
    r = 0.5

    if raetschDataset:
        #-------------------------------------------------------------------------------------------------------------------
        # code for Banana, Breast Cancer, Titanic, Waveform, German. Image datasets.

        # select dataset to classify
        dataset = "breast_cancer/breast-cancer"
        #dataset = "german/german"
        #dataset = "banana/banana"
        #dataset = "image/image"
        #dataset = "waveform/waveform"
        #dataset = "titanic/titanic"

        class_rate = []
        numOfIndices = []

        for i in range (0,10):
            print("Data/Training Set number:", i)
            #filenames
            test_f = "datasets/"+dataset+"_test_data_"+str(i+1)+".asc"
            #print test_f
            test_label_f = "datasets/"+dataset+"_test_labels_"+str(i+1)+".asc"
            #print test_label_f
            train_f = "datasets/"+dataset+"_train_data_"+str(i+1)+".asc"
            #print train_f
            train_label_f = "datasets/"+dataset+"_train_labels_"+str(i+1)+".asc"
            #print train_label_f

            x, t, x_test, t_test = loadData(test_f,test_label_f,train_f,train_label_f)
            weights, indices = rvm(x,t,r)
            numOfIndices.append(len(indices))

            ## Build Test Phi
            K = len(indices)
            N = len(x_test)

            Phi = buildPhi(r,x_test,x[indices])

            # Check Performance
            y_pred = np.dot(Phi,weights)
            check = [(y_pred[k]>0) == t_test[k] for k in range(0,len(t_test))]
            class_rate.append(float(sum(check))/len(t_test))
        #print("Classification rate on test data with: " +str(N)+" data points is: "+str(class_rate))
        #print("# of RVMs on test data: " +str(numOfIndices))

        print("*-----------------------------------------------------------------------------*")
        print("Mean Error Rate on training data with N=" +str(x.shape[0])+" data points and d="+str(x.shape[1])+" features is: "+"%.3f" %(1-float(sum(class_rate))/len(class_rate)))
        print("Mean # of RVMs on test data with N=" +str(N)+" data points is: "+str(float(sum(numOfIndices))/len(numOfIndices)))

        #-------------------------------------------------------------------------------------------------------------------

    else:
        data_train, x, t, x_test, t_test = loadRipleysData()
        #x, t, x_test, t_test = loadPimaData()
        weights, indices = rvm(x,t,r)

        ## Build Test Phi
        K = len(indices)
        N = len(x_test)

        Phi = buildPhi(r,x_test,x[indices])

        # Check Performance
        y_pred = np.dot(Phi,weights)
        check = [(y_pred[k]>0) == t_test[k] for k in range(0,len(t_test))]
        classification_rate = float(sum(check))/len(t_test)
        print("*-----------------------------------------------------------------------------*")
        print("Error rate on training data with N=" +str(x.shape[0])+" data points and d="+str(x.shape[1])+" features is: "+"%.3f" % (1-classification_rate))
        print("#RVMs on test data with N=" +str(N)+" data points is: "+str(K))


    ##### Plotting
    # Plot Points
    pos_examples = np.array([data[0:len(x[0]-1)] for data in data_train if int(data[len(x[0]-1)]) == 0])
    neg_examples = np.array([data[0:len(x[0]-1)] for data in data_train if int(data[len(x[0]-1)]) == 1])
    plt.plot (pos_examples[:,0], pos_examples[:,1], 'rx')
    plt.plot (neg_examples[:,0], neg_examples[:,1], 'bo')
    plt.scatter (x[indices,0],x[indices,1],s=100, facecolors='none', edgecolors='r')
    plt.show(block = False)
    # Plot the decision boundary
    # Generate the mesh
    steps = 50
    x_min, x_max = x[:, 0].min(), x[:, 0].max() 
    y_min, y_max = x[:, 1].min(), x[:, 1].max()
    h_x = (x_max-x_min)/steps
    h_y = (y_max-y_min)/steps
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h_x),
                         np.arange(y_min, y_max, h_y))
    x_grid = np.c_[xx.ravel(), yy.ravel()]

    # Calculate values for each grid point
    PhiGrid = buildPhi(r,x_grid,x[indices])
    y_grid = np.dot(PhiGrid, weights)
    sigmoid    = np.vectorize(sigma)
    # apply sigmoid for probabilites
    p_grid = sigmoid(y_grid)
    p_grid = p_grid.reshape(xx.shape)
    CS = plt.contour(xx,yy,p_grid,levels=[0.25,0.5,0.75],linewidths=2,labels=["p=0.25","p=0.5","p=0.75"], colors=['green', 'black', 'green'],linestyles=['dashed','solid','dashed'])
    #### Colormesh to show classification probabilities
    #plt.pcolormesh(xx, yy, p_grid,cmap = plt.get_cmap('bwr_r'))
    #plt.colorbar()
    labels = ['p=0.25', 'p=0.5','p=0.75']
    for i in range(len(labels)):
        CS.collections[i].set_label(labels[i])
    plt.legend(loc='upper left')
    plt.show(block = False)
    plt.title("RVM Classification")
    plt.xlim([xx.min(),xx.max()])
    plt.ylim([yy.min(),yy.max()])
    plt.show()#(block = False)
    
    
def buildPhi(r,x1,x2):
    N = len(x1)
    K = len(x2)
    Phi = np.zeros((N,K))
    for m in range(0,N):
        for n in range(0,K):
            Phi[m,n] = gaussianKernel(r,x1[m],x2[n])
    return(Phi)

def rvm(x,t,r):
    ## By David Huebner
    # x = data, t = labels, r = hyperparameter for gaussian kernel
    # The Core of the algorithm. It consists of two nested loops.
    
    # The outer loop is adjusting the hyperparameter alpha and determines which indices are used.
    # The criteria to select those "useful" indices is that those indices where alpha is greater than alpha_threshold are neglected.
    # The idea behind this is that a low alpha value implies a higher importance.

    # The inner loop is then minimizing the log posterior probability given the current values of the hyperparameter alpha
    # This is done by iteratively applying Newton's Method which is similar to a steepest descent approach with the aim to adjust the weights w

    ############## List of Variables and Initialisation ################

    LAMBDA_MIN	= 2**(-10)
    GRAD_STOP = 10**(-6)
    ALPHA_THRESHOLD = 10**9
    N = len(x)
   
    # Initial weights and hyperparameters alpha
    w = np.zeros(N+1)
    alpha = N**(-2)*np.ones(N+1) # I took this initial value 1/N^2 from the matlab implementation, but it does not really matter

    # sigmoid applies the sigma function (1/(1+math.exp(-y))) to every element of a matrix   
    sigmoid    = np.vectorize(sigma)

    # Create "design matrix" Phi as after formula(4) in Tipping 2001
    # Contains N rows [phi_1, ..., phi_N] with entries phi_n = [1,K(x_1,x_n),...,K(x_1,x_N)]
    Complete_Phi = np.ones((N,N+1))
    Complete_Phi[:,1:] = buildPhi(r,x,x)

    # indices stores those indices which are used. This concept is called "pruning" and can be found in appending B.1 Numerical Accuracy
    indices = [i for i in range(0,N+1)]
    K = len(indices)
    
    iteration_count = 0
    ### Status
    
    ########## Start outer Loop ############
    while(iteration_count<=500): # Convergence Criteria: Either 500 iterations or alphas do not change much anymore.
        
        # Select those alpha, w and parts of Phi which are used. The other ones are neglected.
        alpha_used = alpha[indices]
        w_used = w[indices]
        Phi = Complete_Phi[:,indices]

        # A as after formula (13) in Tipping 2001
        A = alpha_used * np.identity(K)

        ## This part computes the likelihood as in formula (24) in Tipping 2001
        # The aim is of course to maximize the likelihood, or here to minimize (-1)*likelihhod.         
        Phiw = np.dot(Phi,w_used)
        ## Fix rounding errors to avoid math domain error part 1
        Phiw[Phiw<-500] = -500
        Y = sigmoid(Phiw)
        ## Fix rounding erros to avoid math domain error part 2
        Y[Y==1.0] = 1.0-(1e-16)
        zero_class_log = [math.log(Y[k]) for k in range(0,N) if t[k] == 1]
        one_class_log = [math.log(1-Y[k]) for k in range(0,N) if t[k] == 0]
        data_term = -(sum(zero_class_log)+sum(one_class_log))
        regulariser = 0.5*np.dot(np.dot(w_used,A),w_used)
        err_old = data_term + regulariser
        #pdb.set_trace()
        ########## Inner Loop ##########
        # Implementation of the Newton's Method to update the weigths w
        for i in range(0,25): # More than 25 iteration should not be neccesary. The error normally converges quickly.
        
            # Using Equation (25) in Tipping 2001 to compute the matrix Sigma = (Phi^T*B*Phi+A)^-1
            Phiw = np.dot(Phi,w_used)
            ## Fix rounding errors to avoid math domain error part 1
            Phiw[Phiw<-500] = -500
            Y = sigmoid(Phiw)
            ## Fix rounding erros to avoid math domain error part 2
            Y[Y==1.0] = 1.0-(1e-16)
            beta = [Y[n]*(1-Y[n]) for n in range(0,N)]
            B = beta*np.identity((N))
            Hessian = np.dot(np.dot(np.transpose(Phi),B),Phi)+A
            Sigma = np.linalg.inv(Hessian)

            # Calculate the gradient Phi*(t-Y)
            e = np.subtract(t,Y)
            g = np.dot(np.transpose(Phi),e) - np.array(alpha_used)*np.array(w_used)

            # Solve linear system
            delta_w = np.dot(Sigma,g)
            
            # Step length
            lamb = 1
            while lamb > LAMBDA_MIN:
                # Calculate the error again for the step length lambda
                w_new = w_used + lamb*np.array(delta_w)
                Phiw = np.dot(Phi,w_new)
                ## Fix rounding errors to avoid math domain error part 1
                Phiw[Phiw<-500] = -500
                Y = sigmoid(Phiw)
                ## Fix rounding erros to avoid math domain error part 2
                Y[Y==1.0] = 1.0-(1e-16)
                zero_class_log = [math.log(Y[k]) for k in range(0,N) if t[k] == 1]
                one_class_log = [math.log(1-Y[k]) for k in range(0,N) if t[k] == 0]
                data_term = -(sum(zero_class_log)+sum(one_class_log))/N
                w_squared = [k**2 for k in w_new]
                regulariser = np.dot(alpha_used,w_squared)/(2*N)
                err_new = data_term + regulariser

                # If the error has been reduced, then accept the step. Else, reduce the length lambda of the step
                if err_new > err_old:
                    lamb = lamb/2
                else:                    
                    break
            w_used = w_new
            err_old = err_new
            # If the gradient is too small, then stop iterating
            if np.linalg.norm(g)/K < GRAD_STOP:
                break

        # Updates weigths
        w[indices] = w_used
        
        # Update hyperparameters using equation (16) in Tipping 2001
        gamma = [(1-alpha_used[i]*Sigma[i,i]) for i in range(0,K)]
        old_alpha = list(alpha)
        alpha[indices]  =  np.array([gamma[i]*(w_used[i]**(-2)) for i in range(0,K)])

        # Convergence Criteria if alpha does not change enough anymore
        #difference = np.array([old_alpha[k]-alpha[k] for k in indices])
        #if (max(abs(difference)) < 1):
        #    break        

        # Update useful indices
        indices = [k for k in range(0,N+1) if alpha[k] < ALPHA_THRESHOLD]
        K = len(indices)

        # Delete those weigths which are not useful
        not_used_indices = list(set(range(0,N))-set(indices))
        w[not_used_indices] = 0
        

        if (iteration_count % 50 == 0):
            print("Status: Iteration: "+str(iteration_count)+" Useful indices: "+str(K))
        
        iteration_count = iteration_count + 1
        
    print("Optimization for this training set has finished.")
    w_used = w[indices]
    # Adjust the counting
    indices = np.array(indices)-1
    
    #Finish. Return those weights which were used in the ends and the according indices
    return(w_used,indices)
    
def gaussianKernel(r,x_m,x_n):
    ''' Returns the Gaussian Kernel defined as K(xm,xn) = exp(-r^(-2) ||xm-xn||)^2)'''
    # This Kernel is used to classify Ripley's synthetic data
    # Based on Formula (30) in Tipping 2001
    # The width parameter r is given as 0.5
    return(math.exp(-(r**(-2)*np.linalg.norm(x_m-x_n)**2)))



def sigma(y):
    ''' Returns 1/(1+exp(-y)) '''
    # Defined before formula (23) in Tipping 2001
    return(1/(1+math.exp(-y)))

#load Ripley's synthetic data
def loadRipleysData():
    data_train = np.loadtxt("datasets/synth.tr",skiprows=1)
    rows,cols = data_train.shape
    x = data_train[:,0:cols-1]
    t = data_train[:,cols-1]

    data_test = np.loadtxt("datasets/synth.te",skiprows=1)
    rows_test,cols_test = data_test.shape
    x_test = data_test[:,0:cols_test-1]
    t_test = data_test[:,cols_test-1]

    return (data_train, x, t, x_test, t_test)

## load Pima data
def loadPimaData():
    ## By Foteini Beligianni
    #-----------------load training data--------------------------
    f = open('datasets/pima.tr')
    f.readline() # skip first line
    data_train = []
    for line in f.readlines():
        data_train.append([i for i in line.split()])
    data_train = np.array(data_train)
    rows,cols = data_train.shape
    x = (data_train[:,0:cols-1]).astype(float)              #convert features' values in float type
    t = [(0,1)[d=='Yes'] for d in data_train[:,cols-1]]     #convert Yes and No to 1 and 0 correspondingly
    f.close()

    #-----------------load test data--------------------------
    f = open('datasets/pima.te')
    f.readline() # skip first line
    data_test = []
    for line in f.readlines():
        data_test.append([i for i in line.split()])
    data_test = np.array(data_test)
    rows_test,cols_test = data_test.shape
    x_test = (data_test[:,0:cols_test-1]).astype(float)         #convert features' values in float type
    t_test= [(0,1)[d=='Yes'] for d in data_test[:,cols_test-1]] # convert Yes, No to 1 and 0 correspondingly
    f.close()
    return (x, t, x_test, t_test)

## load data
def loadData(test_file,test_labels,train_file,train_labels):
    ## By Foteini Beligianni
    x = np.loadtxt(train_file)
    t_temp = np.loadtxt(train_labels)
    t = [(0,1)[d==1] for d in t_temp] # convert 1, -1 to 1 and 0 correspondingly
 
    x_test = np.loadtxt(test_file)
    temp = np.loadtxt(test_labels)
    t_test = [(0,1)[i==1] for i in temp] # convert 1, -1 to 1 and 0 correspondingly

    return (x, t, x_test, t_test)

if __name__ == '__main__':
    main()
