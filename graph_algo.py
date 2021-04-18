"""
Graph Algorithm Library

This file contains all the algorithms used for the GraphBandits simulations.
All algorithms can be used as modules.

"""


import numpy as np
import support_func

with_reset = False


class GraphBanditBaseLine:
    """
    Cyclic algorithm with mean estimation using Laplacian.
    """

    def __init__(self, D, A, mu):
        """
        Parameters
        ----------
        D : Degree matrix
        A : Adjacency matrix
        mu : node-mean vector
        """

        # TODO : Laplacian matrix is still computed for dependence on other quantities. Not used for computation.

        self.reset = with_reset
        self.means = mu
        self.rho = 0.0001
        self.delta = 0.0001

        self.D = D
        self.A = A
        self.L = D-A
        self.dim = len(self.L)
        self.L_rho = self.rho*np.identity(self.dim)

        self.remaining_nodes = [i for i in range(self.dim)]

        self.counter = np.zeros((self.dim, self.dim))
        self.conf_width = np.zeros(self.dim)
        self.total_reward = np.zeros(self.dim)
        self.mean_estimate = np.zeros(self.dim)

        self.beta_tracker = 0.0
        self.global_tracker_conf_width = []
        self.inverse_tracker = []
        self.picking_order = []
        self.det_tracker = []

        self.initialize_conf_width()

    def required_reset(self):
        """
        Reset all the arm-counter to 0.
        """
        if self.reset:
            self.counter = np.zeros((self.dim, self.dim))

    def update_conf_width(self):
        """
        Update confidence width of all arms.
        """

        # TODO : Update the inverse computation using Sherman-Morrison

        v_t_inverse = np.linalg.inv(self.counter + self.L_rho)
        self.inverse_tracker.append(v_t_inverse)
        self.det_tracker.append(np.linalg.norm(v_t_inverse))
        for i in range(self.dim):
            self.conf_width[i] = np.sqrt(v_t_inverse[i, i])

    def initialize_conf_width(self):
        """
        Initialize the confidence width of all arms.
        """

        # TODO : Current version is based on \lambda addition. Need to switch to better algorithm
        # FIXME : Testing the new alternative instead of commented code.

        # v_t_inverse = np.linalg.inv(self.counter + self.L_rho)
        # self.inverse_tracker.append(v_t_inverse)
        # self.det_tracker.append(np.linalg.norm(v_t_inverse))
        # for i in range(self.dim):
        #     self.conf_width[i] = np.sqrt(v_t_inverse[i, i])

        self.update_conf_width()

    def play_arm(self, index):
        """
        Update counter and reward based on arm played.

        Parameters
        ----------
        index : Arm being played in the current round.

        """

        # FIXME : Testing to remove function "increment_count"

        #self.increment_count(index)
        self.counter[index, index] += 1
        self.update_conf_width()

        reward = support_func.gaussian_reward(self.means[index])
        self.total_reward[index] = self.total_reward[index] + reward

    def select_arm(self):
        """
        Cyclic arm selection from the remaining set of arms.
        """

        # TODO : Switch current algorithm with true cyclic. Currently only works for symmetric graphs.

        remaining_width = np.zeros(self.dim)
        for i in self.remaining_nodes:
            remaining_width[i] = self.conf_width[i]
        play_index = np.argmax(remaining_width)

        self.picking_order.append(play_index)
        self.global_tracker_conf_width.append(remaining_width)

        return play_index

    def estimate_mean(self):
        """
        Estimate mean using quadratic Laplacian closed form expression.
        """

        v_t_inverse = np.linalg.inv(self.counter + self.L_rho)
        self.mean_estimate = np.dot(v_t_inverse, self.total_reward)

    def eliminate_arms(self):
        """
        Eliminate arms based on UCB-style argument.
        """

        # TODO : Need to change log(T) to  log(|A_i|)

        beta = 2*np.sqrt(14*np.log2(2*self.dim*np.trace(self.counter)/self.delta))
        temp_array = np.zeros(self.dim)

        # FIXME : Testing commented out code with alternative.
        # for i in range(self.dim):
        #     if i in self.remaining_nodes:
        #         temp_array[i] = self.mean_estimate[i] - beta*self.conf_width[i]
        for i in self.remaining_nodes:
            temp_array[i] = self.mean_estimate[i] - beta * self.conf_width[i]

        max_value = max(temp_array)
        self.remaining_nodes = [i for i in self.remaining_nodes if self.mean_estimate[i] + beta * self.conf_width[i] >= max_value ]

    def play_round(self, num):
        """
        Play the round:
            1. Selecting arm.
            2. Getting reward.
            3. Estimating mean.
            4. Elimination of suboptimal arms.

        Parameters
        ----------
        num : Number of plays before estimation/elimination happens.

        """
        for i in range(num):
            play_index = self.select_arm()
            self.play_arm(play_index)
        self.estimate_mean()
        self.eliminate_arms()
        self.required_reset()

    # FIXME : Functions after this line are not known to be of any use

    # def check_criteria(self):
    #
    #     beta = 2*np.sqrt(14*np.log2(2*self.dim*np.trace(self.counter)/self.delta))
    #     self.beta_tracker = beta
    #     temp_array = np.zeros(self.dim)
    #
    #     for i in range(self.dim):
    #         if i in self.remaining_nodes:
    #             temp_array[i] = self.mean_estimate[i] - beta*self.conf_width[i]
    #     max_value = max(temp_array)
    #     checking_array = [i for i in self.remaining_nodes if self.mean_estimate[i] +beta*self.conf_width[i] >= max_value ]
    #     if len(checking_array) > 1:
    #         return False
    #     else:
    #         return True
    #
    # def increment_count(self, index):
    #     """
    #     Updates counter based on the arm being played.
    #
    #     Parameters
    #     ----------
    #     index : Arm being played in the current round.
    #
    #     """
    #     self.counter[index, index] += 1
    #     self.update_conf_width()




class GraphBanditEliminationAlgo:
    """
    Spectral bandits [Valko el.at] based graph elimination algorithm with mean estimation using Laplacian.
    """

    def __init__(self, D, A, mu, eta=5.0):
        """

        Parameters
        ----------
        D : Degree matrix
        A : Adjacency matrix
        mu : node-mean vector
        eta : Penalty parameter for mean estimation
        """

        # TODO : Have not added \epsilon for the \beta confidence width factor. Needed or not?

        self.reset = with_reset
        self.means = mu
        self.eta = eta
        self.D = D
        self.A = A
        self.L = D-A
        self.delta = 0.0001
        self.rho = 0.0001
        self.dim = len(self.L)

        self.remaining_nodes = [i for i in range(self.dim)]
        self.L_rho = self.eta*self.L + self.rho*np.identity(self.dim)
        self.counter = np.zeros((self.dim, self.dim))
        self.conf_width = np.zeros(self.dim)
        self.total_reward = np.zeros(self.dim)
        self.mean_estimate = np.zeros(self.dim)

        self.beta_tracker = 0.0
        self.det_tracker = []
        self.counter_tracker = []
        self.inverse_tracker = []
        self.picking_order = []
        self.global_tracker_conf_width = []

        self.initialize_conf_width()

    def required_reset(self):
        """
        Reset all the arm-counter to 0.
        """
        if self.reset:
            self.counter = np.zeros((self.dim, self.dim))

    def update_conf_width(self):
        """
        Update confidence width of all arms.
        """
        v_t_inverse = np.linalg.inv(self.counter + self.L_rho)
        self.inverse_tracker.append(v_t_inverse)
        self.det_tracker.append(np.linalg.norm(v_t_inverse))
        for i in range(self.dim):
            self.conf_width[i] = np.sqrt(v_t_inverse[i, i])

    def initialize_conf_width(self):
        """
        Initialize confidence width of all arms.
        """
        self.update_conf_width()

    def play_arm(self, index):
        """
        Update counter and reward based on arm played.

        Parameters
        ----------
        index : Arm being played in the current round.

        """

        # FIXME : Testing to remove function "increment_count"
        #self.increment_count(index)
        self. counter[index, index] += 1
        current_counter = np.array(self.counter)
        self.counter_tracker.append(current_counter)
        self.update_conf_width()

        reward = support_func.gaussian_reward(self.means[index])
        self.total_reward[index] = self.total_reward[index] + reward

    def select_arm(self):
        """
        Spectral bandits [Valko el.at] based arm sampling from the remaining set of arms.
        """

        remaining_width = np.zeros(self.dim)
        for i in self.remaining_nodes:
            remaining_width[i] = self.conf_width[i]
        play_index = np.argmax(remaining_width)

        self.global_tracker_conf_width.append(remaining_width)
        self.picking_order.append(play_index)

        return play_index

    def estimate_mean(self):
        """
        Estimate mean using quadratic Laplacian closed form expression.
        """

        v_t_inverse = np.linalg.inv(self.counter + self.L_rho)
        self.mean_estimate = np.dot(v_t_inverse, self.total_reward)

    def eliminate_arms(self):
        """
        Eliminate arms based on UCB-style argument.
        """

        # TODO : Need to change log(T) to  log(|A_i|)

        beta = 2*np.sqrt(14*np.log2(2*self.dim*np.trace(self.counter)/self.delta))
        self.beta_tracker = beta
        temp_array = np.zeros(self.dim)

        # FIXME : Testing commented out code with alternative.
        # for i in range(self.dim):
        #     if i in self.remaining_nodes:
        #         temp_array[i] = self.mean_estimate[i] - beta*self.conf_width[i]
        for i in self.remaining_nodes:
            temp_array[i] = self.mean_estimate[0, i] - beta * self.conf_width[i]

        max_value = max(temp_array)
        self.remaining_nodes = [i for i in self.remaining_nodes if self.mean_estimate[0, i] +beta*self.conf_width[i] >= max_value ]

    def play_round(self, num):
        """
        Play the round:
            1. Selecting arm.
            2. Getting reward.
            3. Estimating mean.
            4. Elimination of suboptimal arms.

        Parameters
        ----------
        num : Number of plays before estimation/elimination happens.

        """
        for i in range(num):
            play_index = self.select_arm()
            self.play_arm(play_index)

        self.estimate_mean()
        self.eliminate_arms()
        self.required_reset()

    # FIXME : For the time being, removing the following dynamic changing penalty parameters

    # def change_eta(self, eta):
    #     self.eta = eta
    #     self.L_rho = self.eta*self.L + self.rho*np.identity(self.dim)
    #
    # def increment_count(self, index):
    #     """
    #     Update counter and reward based on arm played.
    #
    #     Parameters
    #     ----------
    #     index : Arm being played in the current round.
    #
    #     """
    #     self. counter[index, index] += 1
    #     current_counter = np.array(self.counter)
    #     self.counter_tracker.append(current_counter)
    #
    #     # FIXME : Testing commented out code alternative
    #     # v_t_inverse = np.linalg.inv(self.counter + self.L_rho)
    #     # self.inverse_tracker.append(v_t_inverse)
    #     # self.det_tracker.append(np.linalg.norm(v_t_inverse))
    #     # for i in range(self.dim):
    #     #     self.conf_width[i] = np.sqrt(v_t_inverse[i, i])
    #     self.update_conf_width()



class GraphBanditEliminationAlgoImpSampling:
    """
    Proposed graph elimination algorithm with mean estimation using Laplacian.
    """

    def __init__(self, D, A, mu, eta=5.0, eps=0.0):
        """

        Parameters
        ----------
        D : Degree matrix
        A : Adjacency matrix
        mu : node-mean vector
        eta : Penalty parameter for mean estimation
        eps : Imperfect graph factor in constant Beta for confidence width computation
        """

        self.reset = with_reset
        self.means = mu
        self.eta = eta
        self.eps = eps
        self.D = D
        self.A = A
        self.L = D-A
        self.rho = 0.0001
        self.dim = len(self.L)

        self.remaining_nodes = [i for i in range(self.dim)]
        self.L_rho = self.eta*self.L + self.rho*np.identity(self.dim)
        self.counter = np.zeros((self.dim, self.dim))
        self.conf_width = np.zeros(self.dim)
        self.total_reward = np.zeros(self.dim)
        self.mean_estimate = np.zeros(self.dim)
        self.delta = 0.0001

        self.beta_tracker = 0.0
        self.det_tracker = []
        self.counter_tracker = []
        self.inverse_tracker = []
        self.picking_order = []
        self.global_tracker_conf_width = []

        self.initialize_conf_width()

    def required_reset(self):
        """
        Reset all the arm-counter to 0.
        """
        if self.reset:
            self.counter = np.zeros((self.dim, self.dim))

    def update_conf_width(self):
        """
        Update confidence width of all arms.
        """
        v_t_inverse = np.linalg.inv(self.counter + self.L_rho)
        self.inverse_tracker.append(v_t_inverse)
        self.det_tracker.append(np.linalg.norm(v_t_inverse))
        for i in range(self.dim):
            self.conf_width[i] = np.sqrt(v_t_inverse[i, i])

    def initialize_conf_width(self):
        """
        Initialize confidence width of all arms.
        """
        self.update_conf_width()

    def play_arm(self, index):
        """
        Update counter and reward based on arm played.

        Parameters
        ----------
        index : Arm being played in the current round.

        """

        # FIXME : Testing to remove function "increment_count"
        # self.increment_count(index)
        self. counter[index, index] += 1
        current_counter = np.array(self.counter)
        self.counter_tracker.append(current_counter)
        self.update_conf_width()

        reward = support_func.gaussian_reward(self.means[index])
        self.total_reward[index] = self.total_reward[index] + reward

    def opti_selection(self):
        """
        Proposed arm selection criteria based on the ensemble reduction of confidence width.
        """

        # TODO : Replace costly inverse computation using Sherman-Morrison formula.
        A = self.remaining_nodes
        options =[]
        for i in A:
            new_add = np.zeros((self.dim, self.dim))
            new_add[i,i] = 1
            current = np.linalg.inv(self.counter + new_add + self.L_rho)
            options.append(current[i,i])
        index = np.argmax(options)
        return np.array(A)[index]

    def opti_selection_backup(self):
        """
        CURRENTLY DEPRECATED

        Select arm based on the alternative optimization equation.
        """

        A = self.remaining_nodes
        options =[]
        v_t_inverse = self.inverse_tracker[-1]
        for i in A:
            current = np.linalg.norm(v_t_inverse[i, :])
            options.append( (current**2)/(1.0 + v_t_inverse[i,i]) )
        index = np.argmax(options)
        return np.array(A)[index]

    def select_arm(self):
        """
        Select arm to play based on proposed ensemble confidence width reduction criteria.
        """
        remaining_width = np.zeros(self.dim)
        for i in self.remaining_nodes:
            remaining_width[i] = self.conf_width[i]
        play_index = self.opti_selection()

        self.global_tracker_conf_width.append(remaining_width)
        self.picking_order.append(play_index)

        return play_index

    def estimate_mean(self):
        """
        Estimate mean using quadratic Laplacian closed form expression.
        """
        v_t_inverse = np.linalg.inv(self.counter + self.L_rho)
        self.mean_estimate = np.dot(v_t_inverse, self.total_reward)

    def eliminate_arms(self):
        """
        Eliminate arms based on UCB-style argument.
        """

        # TODO : Need to change log(T) to  log(|A_i|)
        beta = 2*np.sqrt(14*np.log2(2*self.dim*np.trace(self.counter)/self.delta)) + self.eta*self.eps
        self.beta_tracker = beta
        temp_array = np.zeros(self.dim)

        # FIXME : Testing commented out code with alternative.
        # for i in range(self.dim):
        #     if i in self.remaining_nodes:
        #         temp_array[i] = self.mean_estimate[i] - beta*self.conf_width[i]
        for i in self.remaining_nodes:
            temp_array[i] = self.mean_estimate[0, i] - beta * self.conf_width[i]

        max_value = max(temp_array)
        self.remaining_nodes = [i for i in self.remaining_nodes if self.mean_estimate[0, i] + beta*self.conf_width[i] >= max_value ]

    def play_round(self, num):
        """
        Play the round:
            1. Selecting arm.
            2. Getting reward.
            3. Estimating mean.
            4. Elimination of suboptimal arms.

        Parameters
        ----------
        num : Number of plays before estimation/elimination happens.

        """
        for i in range(num):
            play_index = self.select_arm()
            self.play_arm(play_index)

        self.estimate_mean()
        self.eliminate_arms()
        self.required_reset()

    # FIXME : For the time being, removing the following dynamic changing penalty parameters

    # def change_eta(self, eta):
    #     self.eta = eta
    #     self.L_rho = self.eta*self.L + self.rho*np.identity(self.dim)
    #
    # def increment_count(self, index):
    #     """
    #     Update counter and reward based on arm played.
    #
    #     Parameters
    #     ----------
    #     index : Arm being played in the current round.
    #
    #     """
    #     self. counter[index, index] += 1
    #     current_counter = np.array(self.counter)
    #     self.counter_tracker.append(current_counter)
    #
    #     # FIXME : Testing commented out code alternative
    #     # v_t_inverse = np.linalg.inv(self.counter + self.L_rho)
    #     # self.inverse_tracker.append(v_t_inverse)
    #     # self.det_tracker.append(np.linalg.norm(v_t_inverse))
    #     # for i in range(self.dim):
    #     #     self.conf_width[i] = np.sqrt(v_t_inverse[i, i])
    #     self.update_conf_width()